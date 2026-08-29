
from __future__ import annotations

import json
import math
import os
import random
import signal
import uuid
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from threading import Event, Lock
from typing import Any

import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL_SECONDS = int(os.getenv("SENSOR_INTERVAL_SECONDS", "10"))
MQTT_QOS = int(os.getenv("MQTT_QOS", "1"))
SCENARIO = os.getenv("SENSOR_SCENARIO", "normal")
RANDOM_SEED = os.getenv("SENSOR_RANDOM_SEED")
RUN_ID = os.getenv("SENSOR_RUN_ID") or uuid.uuid4().hex[:10]
STATION_CATALOG_PATH = Path(os.getenv("STATION_CATALOG_PATH", "/app/data/stations.json"))
VIETNAM_TZ = timezone(timedelta(hours=7))
stop_event = Event()
ventilation_lock = Lock()
active_ventilation: dict[str, dict[str, Any]] = {}
PM25_CLEAN_TARGET = float(os.getenv("VENTILATION_PM25_CLEAN_TARGET", "15"))
CO2_CLEAN_TARGET = float(os.getenv("VENTILATION_CO2_CLEAN_TARGET", "450"))
PM25_DECAY_RATE = float(os.getenv("VENTILATION_PM25_DECAY_RATE", "0.08"))
CO2_DECAY_RATE = float(os.getenv("VENTILATION_CO2_DECAY_RATE", "0.06"))

if RANDOM_SEED is not None:
    random.seed(int(RANDOM_SEED))


def load_stations() -> list[dict[str, Any]]:
    with STATION_CATALOG_PATH.open("r", encoding="utf-8") as file:
        stations = json.load(file)
    return [station for station in stations if station.get("station_id")]



def is_rush_hour(now: datetime) -> bool:
    return 7 <= now.hour <= 9 or 16 <= now.hour <= 18


def location_factor(location_type: str) -> float:
    factors = {
        "main_gate": 8,
        "parking": 12,
        "main_road": 15,
        "park": -8,
        "sport_area": 0,
    }
    return factors.get(location_type, 0)


def scenario_adjustment(station: dict[str, Any], counter: int, now: datetime) -> float:
    if SCENARIO == "rush-hour":
        return 18
    if SCENARIO == "spike" and station["station_id"] == "S03":
        return 45
    if SCENARIO == "recovery" and station["station_id"] == "S03":
        return max(0, 45 - counter * 3)
    if SCENARIO == "normal":
        return 12 if is_rush_hour(now) else 0
    return 0


def should_skip_station(station_id: str) -> bool:
    return SCENARIO == "station-silence" and station_id == os.getenv("SILENT_STATION_ID", "S05")


def simulate_pm25(station: dict[str, Any], counter: int, now: datetime) -> tuple[float, dict[str, float]]:
    base = float(station.get("base_pm25", 35))
    loc = location_factor(str(station.get("location_type", "")))
    wind_speed = random.uniform(0.5, 4.5)
    rainfall = random.choice([0, 0, 0, 1])
    weather_effect = -1.5 * wind_speed - (8 if rainfall else 0)
    noise = random.gauss(0, 3)
    value = base + loc + scenario_adjustment(station, counter, now) + weather_effect + noise
    weather = {
        "temperature": round(random.uniform(28, 35), 1),
        "humidity": float(random.randint(55, 85)),
        "wind_speed": round(wind_speed, 1),
        "rainfall": float(rainfall),
        # Separate environmental metrics; this is not the PM2.5 random noise above.
        "co2": round(max(420, 560 + loc * 13 + scenario_adjustment(station, counter, now) * 6 + random.gauss(0, 25)), 1),
        "noise_db": round(max(35, min(105, 50 + loc * 1.6 + (10 if SCENARIO == "rush-hour" else 0) + random.gauss(0, 4))), 1),
    }
    return round(max(1, value), 2), weather


def apply_ventilation_feedback(
    station_id: str,
    pm25: float,
    co2: float,
    now: datetime,
) -> tuple[float, float]:
    """Apply the Task-4 demo decay only while an approved simulated cycle is active."""
    with ventilation_lock:
        state = active_ventilation.get(station_id)
        if state is None:
            return pm25, co2
        ends_at = datetime.fromisoformat(str(state["ends_at"]))
        if now.astimezone(UTC) >= ends_at.astimezone(UTC):
            active_ventilation.pop(station_id, None)
            return pm25, co2
        if state.get("baseline_pm25") is None:
            state["baseline_pm25"] = float(pm25)
            state["baseline_co2"] = float(co2)
        started_at = datetime.fromisoformat(str(state["started_at"]))
        elapsed_minutes = max(
            0.0,
            (now.astimezone(UTC) - started_at.astimezone(UTC)).total_seconds() / 60.0,
        )
        intensity_scale = max(0.1, float(state.get("intensity_percent") or 80) / 80.0)
        baseline_pm25 = max(PM25_CLEAN_TARGET, float(state["baseline_pm25"]))
        baseline_co2 = max(CO2_CLEAN_TARGET, float(state["baseline_co2"]))
        reduced_pm25 = (
            (baseline_pm25 - PM25_CLEAN_TARGET)
            * math.exp(-PM25_DECAY_RATE * intensity_scale * elapsed_minutes)
            + PM25_CLEAN_TARGET
        )
        reduced_co2 = (
            (baseline_co2 - CO2_CLEAN_TARGET)
            * math.exp(-CO2_DECAY_RATE * intensity_scale * elapsed_minutes)
            + CO2_CLEAN_TARGET
        )
        return round(min(pm25, reduced_pm25), 2), round(min(co2, reduced_co2), 1)


def handle_device_status(raw: dict[str, Any]) -> None:
    station_id = str(raw.get("station_id") or "").upper()
    mode = str(raw.get("device_state") or "").upper()
    if station_id not in {"S01", "S02", "S03", "S04", "S05"}:
        return
    with ventilation_lock:
        if raw.get("status") not in {"succeeded", "duplicate"}:
            return
        if mode not in {"RUNNING_BOOST", "AIR_PURIFIER_ON"}:
            active_ventilation.pop(station_id, None)
            return
        started_at = raw.get("started_at") or raw.get("timestamp")
        ends_at = raw.get("ends_at")
        duration_minutes = raw.get("duration_minutes")
        if not ends_at and started_at and duration_minutes:
            ends_at = (
                datetime.fromisoformat(str(started_at)).astimezone(UTC)
                + timedelta(minutes=int(duration_minutes))
            ).isoformat()
        if not started_at or not ends_at:
            return
        active_ventilation[station_id] = {
            "device_id": raw.get("device_id"),
            "command_id": raw.get("command_id"),
            "started_at": str(started_at),
            "ends_at": str(ends_at),
            "intensity_percent": int(raw.get("intensity_percent") or 80),
            "baseline_pm25": None,
            "baseline_co2": None,
        }


def publish_station_status(client: mqtt.Client, station_id: str, timestamp: str, status: str = "online", reason: str | None = None) -> None:
    topic = f"airguard/stations/{station_id}/status"
    payload: dict[str, Any] = {"station_id": station_id, "status": status, "timestamp": timestamp, "source": "simulator"}
    if reason:
        payload["reason"] = reason
    client.publish(topic, json.dumps(payload, ensure_ascii=True), qos=MQTT_QOS)
    print(f"status topic={topic} station={station_id} status={status}", flush=True)


def publish_measurement(client: mqtt.Client, station: dict[str, Any], counter: int, timestamp: str, duplicate: bool = False) -> None:
    station_id = station["station_id"]
    now = datetime.fromisoformat(timestamp)
    pm25, weather = simulate_pm25(station, counter, now)
    pm25, weather["co2"] = apply_ventilation_feedback(
        station_id,
        pm25,
        float(weather["co2"]),
        now,
    )
    message_counter = counter - 1 if duplicate and counter > 1 else counter
    topic = f"airguard/stations/{station_id}/measurements"
    payload = {
        "message_id": f"MSG-{RUN_ID}-{station_id}-{message_counter:06d}",
        "station_id": station_id,
        "pm25": pm25,
        "timestamp": timestamp,
        "source": "simulator",
        **weather,
    }
    client.publish(topic, json.dumps(payload, ensure_ascii=True), qos=MQTT_QOS)
    print(f"measurement topic={topic} message_id={payload['message_id']} station={station_id} pm25={pm25} scenario={SCENARIO}", flush=True)


def request_stop(signum, frame) -> None:
    print(f"Stopping simulator after signal {signum}...", flush=True)
    stop_event.set()


def main() -> None:
    if MQTT_QOS not in {0, 1, 2}:
        raise ValueError("MQTT_QOS must be 0, 1, or 2")

    stations = load_stations()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(connected_client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            connected_client.subscribe("airguard/devices/+/status", qos=MQTT_QOS)

    def on_message(_client, _userdata, message):
        try:
            handle_device_status(json.loads(message.payload.decode("utf-8")))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"device-status ignored reason={type(exc).__name__}", flush=True)

    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    print(f"Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT}; scenario={SCENARIO}", flush=True)

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    counter = 0
    try:
        while not stop_event.is_set():
            counter += 1
            timestamp = datetime.now(VIETNAM_TZ).isoformat()
            for station in stations:
                station_id = station["station_id"]
                if should_skip_station(station_id):
                    publish_station_status(client, station_id, timestamp, "offline", "station_silence_scenario")
                    continue
                publish_measurement(client, station, counter, timestamp)
                publish_station_status(client, station_id, timestamp)
                if SCENARIO == "duplicate" and station_id == "S03" and counter % 3 == 0:
                    publish_measurement(client, station, counter, timestamp, duplicate=True)
            stop_event.wait(INTERVAL_SECONDS)

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
