from __future__ import annotations

import json
import logging
import signal
import time
import os
import urllib.error
import urllib.request
from threading import Event
from typing import Any

import paho.mqtt.client as mqtt

from .config import ConsumerSettings
from .station_catalog import StationCatalog
from .storage import PostgresStore
from .validator import (
    MEASUREMENT_TOPIC_RE,
    STATUS_TOPIC_RE,
    DEVICE_STATUS_TOPIC_RE,
    ValidationErrorCode,
    validate_device_status_message,
    validate_measurement_message,
    validate_status_message,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("airguard.mqtt_consumer")
stop_event = Event()
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")


def trigger_alert_evaluation(station_id: str, correlation_id: str) -> None:
    """Notify backend after DB commit; ingestion remains durable if API is unavailable."""
    body = json.dumps({"station_id": station_id}).encode("utf-8")
    request = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/internal/ingestion/evaluate-alerts",
        data=body,
        headers={"Content-Type": "application/json", "X-Request-ID": correlation_id},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            if response.status >= 300:
                logger.warning("alert evaluation rejected station=%s status=%s", station_id, response.status)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("alert evaluation unavailable station=%s error=%s", station_id, exc)


def _payload_excerpt(raw_payload: bytes) -> dict[str, Any]:
    try:
        decoded = json.loads(raw_payload.decode("utf-8"))
        if isinstance(decoded, dict):
            return {
                "message_id": decoded.get("message_id"),
                "station_id": decoded.get("station_id"),
                "source": decoded.get("source"),
            }
    except Exception:
        return {}
    return {}


def _station_from_topic(topic: str) -> str | None:
    match = MEASUREMENT_TOPIC_RE.match(topic) or STATUS_TOPIC_RE.match(topic)
    return match.group("station_id") if match else None


def build_client(settings: ConsumerSettings, catalog: StationCatalog, store: PostgresStore) -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=settings.client_id,
        clean_session=False,
        manual_ack=True,
    )
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logger.info("connected mqtt host=%s port=%s", settings.mqtt_host, settings.mqtt_port)
            client.subscribe("airguard/stations/+/measurements", qos=settings.mqtt_qos)
            client.subscribe("airguard/stations/+/status", qos=settings.mqtt_qos)
            client.subscribe("airguard/devices/+/status", qos=settings.mqtt_qos)
        else:
            logger.error("mqtt connect failed reason=%s", reason_code)

    def on_message(client, userdata, message):
        def acknowledge() -> None:
            client.ack(message.mid, message.qos)

        topic = message.topic
        raw_payload = message.payload
        station_id = _station_from_topic(topic)

        if topic.endswith("/measurements"):
            result = validate_measurement_message(
                topic,
                raw_payload,
                catalog,
                stale_after_seconds=settings.stale_after_seconds,
                max_future_skew_seconds=settings.max_future_skew_seconds,
            )
            if not result.accepted or not result.payload:
                store.record_rejection(
                    topic=topic,
                    station_id=station_id,
                    message_id=_payload_excerpt(raw_payload).get("message_id"),
                    reason=result.reason or ValidationErrorCode.MALFORMED,
                    detail=result.detail,
                    payload=_payload_excerpt(raw_payload),
                )
                logger.warning("rejected measurement topic=%s reason=%s detail=%s", topic, result.reason, result.detail)
                acknowledge()
                return

            persist_result = store.persist_measurement(result.payload)
            if persist_result.duplicate:
                logger.info("duplicate measurement ignored message_id=%s station=%s", result.payload.message_id, result.payload.station_id)
                acknowledge()
                return
            logger.info(
                "accepted measurement message_id=%s station=%s pm25=%s",
                result.payload.message_id,
                result.payload.station_id,
                result.payload.pm25,
            )
            trigger_alert_evaluation(result.payload.station_id, result.payload.message_id)
            acknowledge()
            return

        if topic.endswith("/status"):
            if DEVICE_STATUS_TOPIC_RE.match(topic):
                result = validate_device_status_message(topic, raw_payload)
                if not result.accepted or not result.payload:
                    store.record_rejection(
                        topic=topic,
                        station_id=None,
                        message_id=None,
                        reason=result.reason or ValidationErrorCode.MALFORMED,
                        detail=result.detail,
                        payload=_payload_excerpt(raw_payload),
                    )
                    logger.warning("rejected device status topic=%s reason=%s detail=%s", topic, result.reason, result.detail)
                    acknowledge()
                    return
                if not store.persist_device_status(result.payload):
                    store.record_rejection(
                        topic=topic,
                        station_id=None,
                        message_id=result.payload.command_id,
                        reason=ValidationErrorCode.UNKNOWN_DEVICE,
                        detail="device is not registered in devices master data",
                        payload={"device_id": result.payload.device_id, "command_id": result.payload.command_id},
                    )
                    acknowledge()
                    return
                logger.info("accepted device status device=%s status=%s", result.payload.device_id, result.payload.status)
                acknowledge()
                return
            result = validate_status_message(
                topic,
                raw_payload,
                catalog,
                stale_after_seconds=settings.stale_after_seconds,
                max_future_skew_seconds=settings.max_future_skew_seconds,
            )
            if not result.accepted or not result.payload:
                store.record_rejection(
                    topic=topic,
                    station_id=station_id,
                    message_id=None,
                    reason=result.reason or ValidationErrorCode.MALFORMED,
                    detail=result.detail,
                    payload=_payload_excerpt(raw_payload),
                )
                logger.warning("rejected status topic=%s reason=%s detail=%s", topic, result.reason, result.detail)
                acknowledge()
                return
            store.persist_status(result.payload)
            logger.info("accepted status station=%s status=%s", result.payload.station_id, result.payload.status)
            acknowledge()
            return

        store.record_rejection(
            topic=topic,
            station_id=station_id,
            message_id=None,
            reason=ValidationErrorCode.UNKNOWN_TOPIC,
            detail="topic is not subscribed contract",
            payload=_payload_excerpt(raw_payload),
        )
        acknowledge()

    client.on_connect = on_connect
    client.on_message = on_message
    return client


def _request_stop(signum, frame) -> None:
    logger.info("shutdown requested signal=%s", signum)
    stop_event.set()


def main() -> None:
    settings = ConsumerSettings.load()
    catalog = StationCatalog.load(settings.station_catalog_path)
    store = PostgresStore(settings.database_url)
    client = build_client(settings, catalog, store)

    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    while not stop_event.is_set():
        try:
            client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
            client.loop_start()
            while not stop_event.wait(1):
                pass
        except Exception:
            logger.exception("consumer loop failed; retrying")
            time.sleep(5)
        finally:
            client.loop_stop()
            client.disconnect()


if __name__ == "__main__":
    main()
