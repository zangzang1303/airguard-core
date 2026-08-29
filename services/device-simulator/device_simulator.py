from __future__ import annotations

import json
import logging
import os
import signal
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event, Lock
from typing import Literal

import paho.mqtt.client as mqtt
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("airguard.device_simulator")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_QOS = int(os.getenv("MQTT_QOS", "1"))
DEVICE_ID = os.getenv("DEVICE_ID", "FILTER-01")
STATE_PATH = Path(os.getenv("DEVICE_STATE_PATH", "/data/processed-keys.json"))
stop_event = Event()


def load_processed_keys() -> set[str]:
    try:
        values = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return {str(value) for value in values}
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return set()


processed_keys = load_processed_keys()
device_state = "ECO_MODE"
active_cycle: dict[str, object] | None = None
active_cycle_lock = Lock()


def save_processed_keys() -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = STATE_PATH.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(sorted(processed_keys)), encoding="utf-8")
    temporary_path.replace(STATE_PATH)


class DeviceCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: str = Field(min_length=1, max_length=100)
    device_id: str = Field(min_length=1, max_length=50)
    station_id: str = Field(pattern=r"^S0[1-5]$")
    action: Literal["ventilation_boost", "air_purifier_on", "eco_mode", "standby"]
    approval_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)
    timestamp: datetime
    duration_minutes: int | None = Field(default=None, ge=5, le=180)
    intensity_percent: int | None = Field(default=None, ge=1, le=100)

    @field_validator("timestamp")
    @classmethod
    def timestamp_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("timestamp must include timezone")
        return value

    @model_validator(mode="after")
    def timed_action_has_parameters(self) -> DeviceCommand:
        if self.action in {"ventilation_boost", "air_purifier_on"}:
            if self.duration_minutes is None or self.intensity_percent is None:
                raise ValueError("timed device action requires duration_minutes and intensity_percent")
        return self


def publish_status(
    client: mqtt.Client,
    command_id: str,
    status: str,
    reason: str | None = None,
    *,
    command: DeviceCommand | None = None,
    cycle: dict[str, object] | None = None,
) -> None:
    payload = {
        "command_id": command_id,
        "device_id": DEVICE_ID,
        "status": status,
        "timestamp": datetime.now(UTC).isoformat(),
        "is_simulated": True,
        "device_state": device_state,
    }
    cycle_data = cycle or {}
    if command is not None:
        payload.update(
            {
                "station_id": command.station_id,
                "action": command.action,
                "started_at": command.timestamp.astimezone(UTC).isoformat(),
                "duration_minutes": command.duration_minutes,
                "intensity_percent": command.intensity_percent,
            }
        )
        if command.duration_minutes is not None:
            payload["ends_at"] = (
                command.timestamp.astimezone(UTC) + timedelta(minutes=command.duration_minutes)
            ).isoformat()
    elif cycle_data:
        payload.update(cycle_data)
    if reason:
        payload["reason"] = reason
    topic = f"airguard/devices/{DEVICE_ID}/status"
    client.publish(topic, json.dumps(payload), qos=MQTT_QOS)
    logger.info("device status device=%s command_id=%s status=%s", DEVICE_ID, command_id, status)


def build_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"airguard-device-{DEVICE_ID}")

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            client.subscribe(f"airguard/devices/{DEVICE_ID}/command", qos=MQTT_QOS)
            logger.info("device connected device=%s host=%s port=%s", DEVICE_ID, MQTT_HOST, MQTT_PORT)
        else:
            logger.error("device mqtt connect failed reason=%s", reason_code)

    def on_message(client, userdata, message):
        global active_cycle, device_state
        command_id = "unknown"
        try:
            raw = json.loads(message.payload.decode("utf-8"))
            command_id = str(raw.get("command_id", command_id))
            command = DeviceCommand.model_validate(raw)
            if command.device_id != DEVICE_ID:
                publish_status(client, command.command_id, "rejected", "unknown_device", command=command)
                return
            if command.idempotency_key in processed_keys:
                publish_status(
                    client,
                    command.command_id,
                    "duplicate",
                    "idempotency_key_already_processed",
                    command=command,
                )
                return
            if command.action == "ventilation_boost":
                device_state = "RUNNING_BOOST"
            elif command.action == "air_purifier_on":
                device_state = "AIR_PURIFIER_ON"
            elif command.action == "eco_mode":
                device_state = "ECO_MODE"
            else:
                device_state = "STANDBY"
            with active_cycle_lock:
                active_cycle = None
                if command.duration_minutes is not None:
                    started_at = command.timestamp.astimezone(UTC)
                    active_cycle = {
                        "command_id": command.command_id,
                        "station_id": command.station_id,
                        "action": command.action,
                        "started_at": started_at.isoformat(),
                        "ends_at": (started_at + timedelta(minutes=command.duration_minutes)).isoformat(),
                        "duration_minutes": command.duration_minutes,
                        "intensity_percent": command.intensity_percent,
                    }
            processed_keys.add(command.idempotency_key)
            save_processed_keys()
            publish_status(
                client,
                command.command_id,
                "succeeded",
                "simulated_ack_after_server_approval",
                command=command,
            )
        except Exception as exc:
            publish_status(client, command_id, "rejected", f"invalid_command:{type(exc).__name__}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    return client


def publish_expired_cycle(client: mqtt.Client) -> None:
    global active_cycle, device_state
    with active_cycle_lock:
        cycle = dict(active_cycle) if active_cycle else None
        if not cycle:
            return
        ends_at = datetime.fromisoformat(str(cycle["ends_at"]))
        if datetime.now(UTC) < ends_at:
            return
        active_cycle = None
        device_state = "STANDBY"
    publish_status(
        client,
        str(cycle["command_id"]),
        "succeeded",
        "configured_duration_elapsed",
        cycle={**cycle, "action": "standby"},
    )


def _stop(signum, frame) -> None:
    logger.info("shutdown requested signal=%s", signum)
    stop_event.set()


def main() -> None:
    if MQTT_QOS not in {0, 1, 2}:
        raise ValueError("MQTT_QOS must be 0, 1, or 2")
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    client = build_client()
    while not stop_event.is_set():
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_start()
            while not stop_event.wait(1):
                publish_expired_cycle(client)
        except Exception:
            logger.exception("device loop failed; retrying")
            stop_event.wait(5)
        finally:
            client.loop_stop()
            client.disconnect()


if __name__ == "__main__":
    main()
