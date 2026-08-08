from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConsumerSettings:
    mqtt_host: str
    mqtt_port: int
    mqtt_qos: int
    database_url: str
    station_catalog_path: Path
    stale_after_seconds: int
    max_future_skew_seconds: int
    client_id: str

    @classmethod
    def load(cls) -> "ConsumerSettings":
        mqtt_qos = int(os.getenv("MQTT_QOS", "1"))
        if mqtt_qos not in {0, 1, 2}:
            raise ValueError("MQTT_QOS must be 0, 1, or 2")

        stale_after_seconds = int(os.getenv("STALE_AFTER_SECONDS", "300"))
        if stale_after_seconds <= 0:
            raise ValueError("STALE_AFTER_SECONDS must be positive")

        max_future_skew_seconds = int(os.getenv("MAX_FUTURE_SKEW_SECONDS", "60"))
        if max_future_skew_seconds < 0:
            raise ValueError("MAX_FUTURE_SKEW_SECONDS cannot be negative")

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL is required for mqtt-consumer")

        return cls(
            mqtt_host=os.getenv("MQTT_HOST", "localhost"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
            mqtt_qos=mqtt_qos,
            database_url=database_url,
            station_catalog_path=Path(os.getenv("STATION_CATALOG_PATH", "/app/data/stations.json")),
            stale_after_seconds=stale_after_seconds,
            max_future_skew_seconds=max_future_skew_seconds,
            client_id=os.getenv("MQTT_CONSUMER_CLIENT_ID", "airguard-mqtt-consumer"),
        )
