from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

CONSUMER_PATH = Path(__file__).resolve().parents[2] / "services" / "mqtt-consumer"
sys.path.insert(0, str(CONSUMER_PATH))

from mqtt_consumer.schemas import MeasurementPayload, StationStatusPayload  # noqa: E402
from mqtt_consumer.storage import PostgresStore  # noqa: E402


class FakeCursor:
    def __init__(self, *, inserted: bool = True) -> None:
        self.inserted = inserted
        self.statements: list[tuple[str, tuple[object, ...] | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def execute(self, statement: str, params=None) -> None:
        self.statements.append((statement, params))

    def fetchone(self):
        if any("INSERT INTO measurements" in statement for statement, _ in self.statements):
            return {"measurement_id": 7} if self.inserted else None
        return None


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.cursor_instance = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def cursor(self, **_kwargs):
        return self.cursor_instance


def measurement() -> MeasurementPayload:
    return MeasurementPayload(
        message_id="MSG-S01-1",
        station_id="S01",
        pm25=42.5,
        timestamp=datetime(2026, 8, 3, 8, 0, tzinfo=UTC),
        source="simulator",
    )


def test_duplicate_measurement_is_not_persisted_or_reprocessed() -> None:
    cursor = FakeCursor(inserted=False)
    store = PostgresStore("unused")
    store._connect = lambda: FakeConnection(cursor)  # type: ignore[method-assign]

    result = store.persist_measurement(measurement())

    assert result.accepted is False
    assert result.duplicate is True
    assert sum("INSERT INTO measurements" in statement for statement, _ in cursor.statements) == 1
    assert sum("INSERT INTO mqtt_rejections" in statement for statement, _ in cursor.statements) == 1
    assert not any("INSERT INTO station_status" in statement for statement, _ in cursor.statements)


def test_offline_then_newer_online_status_is_persisted() -> None:
    cursor = FakeCursor()
    store = PostgresStore("unused")
    store._connect = lambda: FakeConnection(cursor)  # type: ignore[method-assign]

    store.persist_status(
        StationStatusPayload(
            station_id="S01",
            status="offline",
            timestamp=datetime(2026, 8, 3, 8, 0, tzinfo=UTC),
            source="simulator",
            reason="station_silence_scenario",
        )
    )
    store.persist_status(
        StationStatusPayload(
            station_id="S01",
            status="online",
            timestamp=datetime(2026, 8, 3, 8, 0, 1, tzinfo=UTC),
            source="simulator",
            reason="heartbeat",
        )
    )

    status_writes = [
        params for statement, params in cursor.statements if "INSERT INTO station_status" in statement
    ]
    assert len(status_writes) == 2
    assert status_writes[0][1] == "offline"
    assert status_writes[1][1] == "online"
