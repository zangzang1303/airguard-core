from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

CONSUMER_PATH = Path(__file__).resolve().parents[2] / "services" / "mqtt-consumer"
sys.path.insert(0, str(CONSUMER_PATH))

from mqtt_consumer.schemas import DeviceStatusPayload, MeasurementPayload, StationStatusPayload  # noqa: E402
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


class DeviceStatusCursor(FakeCursor):
    def __init__(
        self,
        *,
        matched: bool,
        intent_status: str = "published",
        acknowledged_at: datetime | None = None,
        ack_status: str | None = None,
        device_state: str | None = None,
    ) -> None:
        super().__init__()
        self.matched = matched
        self.intent_status = intent_status
        self.acknowledged_at = acknowledged_at
        self.ack_status = ack_status
        self.device_state = device_state

    def fetchone(self):
        statement = self.statements[-1][0]
        if "SELECT device_id FROM devices" in statement:
            return {"device_id": "FILTER-01"}
        if "SELECT command_intent_id" in statement:
            if not self.matched:
                return None
            return {
                "command_intent_id": "11111111-1111-1111-1111-111111111111",
                "approval_request_id": "22222222-2222-2222-2222-222222222222",
                "status": self.intent_status,
                "acknowledged_at": self.acknowledged_at,
                "ack_status": self.ack_status,
                "device_state": self.device_state,
                "dispatch_error": None,
            }
        return None


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


def test_matched_device_ack_updates_intent_and_persists_idempotent_status_event() -> None:
    cursor = DeviceStatusCursor(matched=True)
    store = PostgresStore("unused")
    store._connect = lambda: FakeConnection(cursor)  # type: ignore[method-assign]
    observed_at = datetime(2026, 8, 3, 8, 5, tzinfo=UTC)

    accepted = store.persist_device_status(
        DeviceStatusPayload(
            command_id="cmd-1",
            device_id="FILTER-01",
            status="succeeded",
            timestamp=observed_at,
            is_simulated=True,
            device_state="RUNNING_BOOST",
        )
    )

    assert accepted is True
    intent_statement, intent_params = next(
        (statement, params)
        for statement, params in cursor.statements
        if "UPDATE device_command_intents" in statement
    )
    assert "acknowledged_at" in intent_statement
    assert "ack_status" in intent_statement
    assert "device_state" in intent_statement
    assert intent_params is not None
    assert observed_at in intent_params
    assert "RUNNING_BOOST" in intent_params
    assert any("UPDATE devices" in statement for statement, _ in cursor.statements)

    event_statement, event_params = next(
        (statement, params)
        for statement, params in cursor.statements
        if "INSERT INTO device_status_events" in statement
    )
    assert "ON CONFLICT (device_id, command_id, status) DO NOTHING" in event_statement
    assert event_params == (
        "cmd-1",
        "11111111-1111-1111-1111-111111111111",
        "FILTER-01",
        "succeeded",
        "RUNNING_BOOST",
        None,
        observed_at,
        True,
    )


def test_unmatched_device_ack_persists_event_and_audits_correlation_failure() -> None:
    cursor = DeviceStatusCursor(matched=False)
    store = PostgresStore("unused")
    store._connect = lambda: FakeConnection(cursor)  # type: ignore[method-assign]

    accepted = store.persist_device_status(
        DeviceStatusPayload(
            command_id="unknown-command",
            device_id="FILTER-01",
            status="rejected",
            timestamp=datetime(2026, 8, 3, 8, 5, tzinfo=UTC),
            is_simulated=True,
            device_state="ECO_MODE",
            reason="unknown_command",
        )
    )

    assert accepted is True
    assert not any("UPDATE device_command_intents" in statement for statement, _ in cursor.statements)
    assert not any("UPDATE devices" in statement for statement, _ in cursor.statements)
    event_params = next(
        params for statement, params in cursor.statements if "INSERT INTO device_status_events" in statement
    )
    assert event_params is not None and event_params[1] is None
    audit_params = next(
        params for statement, params in cursor.statements if "INSERT INTO audit_logs" in statement
    )
    assert audit_params is not None
    assert audit_params[1] == "device_command.ack.unmatched"
    assert audit_params[4] == "failure"


def test_late_rejection_does_not_downgrade_succeeded_intent_or_device_state() -> None:
    acknowledged_at = datetime(2026, 8, 3, 8, 10, tzinfo=UTC)
    cursor = DeviceStatusCursor(
        matched=True,
        intent_status="succeeded",
        acknowledged_at=acknowledged_at,
        ack_status="succeeded",
        device_state="RUNNING_BOOST",
    )
    store = PostgresStore("unused")
    store._connect = lambda: FakeConnection(cursor)  # type: ignore[method-assign]

    accepted = store.persist_device_status(
        DeviceStatusPayload(
            command_id="cmd-1",
            device_id="FILTER-01",
            status="rejected",
            timestamp=acknowledged_at - timedelta(minutes=1),
            is_simulated=True,
            device_state="ECO_MODE",
            reason="late_replayed_failure",
        )
    )

    assert accepted is True
    assert not any("UPDATE devices" in statement for statement, _ in cursor.statements)
    intent_params = next(
        params for statement, params in cursor.statements if "UPDATE device_command_intents" in statement
    )
    assert intent_params == (
        "succeeded",
        acknowledged_at,
        "succeeded",
        "RUNNING_BOOST",
        None,
        "11111111-1111-1111-1111-111111111111",
    )
