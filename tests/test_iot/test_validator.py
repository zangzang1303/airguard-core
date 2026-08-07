from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CONSUMER_PATH = Path(__file__).resolve().parents[2] / "services" / "mqtt-consumer"
sys.path.insert(0, str(CONSUMER_PATH))

from mqtt_consumer.station_catalog import StationCatalog
from mqtt_consumer.validator import ValidationErrorCode, validate_measurement_message, validate_status_message


def catalog() -> StationCatalog:
    return StationCatalog({"S01": {"station_id": "S01"}, "S02": {"station_id": "S02"}})


def payload(**overrides: object) -> str:
    now = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    data = {
        "message_id": "MSG-S01-1",
        "station_id": "S01",
        "pm25": 42.5,
        "temperature": 31.2,
        "humidity": 70,
        "wind_speed": 2.4,
        "rainfall": 0,
        "timestamp": now.isoformat(),
        "source": "simulator",
    }
    data.update(overrides)
    import json

    return json.dumps(data)


def test_valid_measurement_accepts_contract_payload() -> None:
    now = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    result = validate_measurement_message(
        "airguard/stations/S01/measurements",
        payload(),
        catalog(),
        now=now,
    )

    assert result.accepted is True
    assert result.payload is not None
    assert result.payload.station_id == "S01"
    assert result.payload.source == "simulator"


def test_unknown_station_is_rejected() -> None:
    now = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    result = validate_measurement_message(
        "airguard/stations/S99/measurements",
        payload(station_id="S99", message_id="MSG-S99-1"),
        catalog(),
        now=now,
    )

    assert result.accepted is False
    assert result.reason == ValidationErrorCode.UNKNOWN_STATION


def test_topic_station_mismatch_is_rejected() -> None:
    now = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    result = validate_measurement_message(
        "airguard/stations/S02/measurements",
        payload(station_id="S01"),
        catalog(),
        now=now,
    )

    assert result.accepted is False
    assert result.reason == ValidationErrorCode.TOPIC_STATION_MISMATCH


def test_negative_pm25_is_rejected_as_range_error() -> None:
    now = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    result = validate_measurement_message(
        "airguard/stations/S01/measurements",
        payload(pm25=-1),
        catalog(),
        now=now,
    )

    assert result.accepted is False
    assert result.reason == ValidationErrorCode.RANGE_ERROR


def test_future_timestamp_is_rejected() -> None:
    now = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    result = validate_measurement_message(
        "airguard/stations/S01/measurements",
        payload(timestamp=(now + timedelta(minutes=5)).isoformat()),
        catalog(),
        now=now,
        max_future_skew_seconds=30,
    )

    assert result.accepted is False
    assert result.reason == ValidationErrorCode.FUTURE_TIME


def test_stale_timestamp_is_rejected() -> None:
    now = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    result = validate_measurement_message(
        "airguard/stations/S01/measurements",
        payload(timestamp=(now - timedelta(minutes=10)).isoformat()),
        catalog(),
        now=now,
        stale_after_seconds=120,
    )

    assert result.accepted is False
    assert result.reason == ValidationErrorCode.STALE


def test_valid_station_status_accepts_source_and_timezone() -> None:
    now = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    result = validate_status_message(
        "airguard/stations/S01/status",
        '{"station_id":"S01","status":"online","timestamp":"2026-08-03T08:00:00+00:00","source":"simulator"}',
        catalog(),
        now=now,
    )

    assert result.accepted is True
    assert result.payload is not None
    assert result.payload.status == "online"
