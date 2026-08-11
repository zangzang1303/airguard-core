from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SIMULATOR_PATH = Path(__file__).resolve().parents[2] / "services" / "sensor-simulator"
sys.path.insert(0, str(SIMULATOR_PATH))


class RecordingClient:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str, int]] = []

    def publish(self, topic: str, payload: str, qos: int) -> None:
        self.messages.append((topic, payload, qos))


def test_measurement_message_id_contains_run_id_and_counter(monkeypatch) -> None:
    monkeypatch.setenv("SENSOR_RUN_ID", "run-test-01")
    module = importlib.import_module("sensor_simulator")
    module = importlib.reload(module)
    client = RecordingClient()

    module.publish_measurement(
        client,
        {"station_id": "S01", "base_pm25": 35, "location_type": "main_gate"},
        7,
        datetime.now(timezone.utc).isoformat(),
    )

    payload = json.loads(client.messages[0][1])
    assert payload["message_id"] == "MSG-run-test-01-S01-000007"
    assert payload["source"] == "simulator"


def test_consumer_client_uses_manual_ack() -> None:
    consumer_path = Path(__file__).resolve().parents[2] / "services" / "mqtt-consumer"
    sys.path.insert(0, str(consumer_path))
    from mqtt_consumer.config import ConsumerSettings
    from mqtt_consumer.main import build_client
    from mqtt_consumer.station_catalog import StationCatalog

    settings = ConsumerSettings(
        mqtt_host="localhost",
        mqtt_port=1883,
        mqtt_qos=1,
        database_url="postgresql://example",
        station_catalog_path=Path("data/stations.json"),
        stale_after_seconds=300,
        max_future_skew_seconds=60,
        client_id="test-consumer",
    )
    client = build_client(settings, StationCatalog({"S01": {"station_id": "S01"}}), object())

    assert client._manual_ack is True
