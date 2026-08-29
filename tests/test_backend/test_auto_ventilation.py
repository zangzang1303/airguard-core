from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest

from backend.app.services.alert_engine import AlertEngine
from backend.app.services.approval_service import ApprovalService
from backend.app.services.database import ServiceError
from backend.app.services.ventilation_service import VentilationService


class FakeCursor:
    def __init__(self, db) -> None:
        self.db = db
        self.rows: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, query: str, params) -> None:
        if "FROM station_status" in query:
            self.rows = [{"status": self.db.station_status}] if self.db.station_status else []
            return
        if "FROM measurements" in query:
            station_id, start, end = params
            self.rows = [
                row for row in self.db.measurements
                if row["station_id"] == station_id
                and row["quality_flag"] == "valid"
                and start <= row["measured_at"] <= end
            ]
            self.rows.sort(key=lambda row: row["measured_at"])
            return
        if "FROM device_command_intents" in query:
            station_id = params[0]
            self.rows = [
                row for row in self.db.intents
                if row["station_id"] == station_id
                and row["command"] in {"ventilation_boost", "air_purifier_on"}
                and row["status"] == "succeeded"
                and not row.get("closed", False)
            ]
            self.rows.sort(
                key=lambda row: row.get("dispatched_at") or row["created_at"],
                reverse=True,
            )
            self.rows = self.rows[:1]
            return
        raise AssertionError(query)

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FakeConnection:
    def __init__(self, db) -> None:
        self.db = db

    def cursor(self, **_kwargs):
        return FakeCursor(self.db)


class FakeDatabase:
    def __init__(
        self,
        measurements: list[dict],
        intents: list[dict] | None = None,
        *,
        station_status: str | None = "online",
    ) -> None:
        self.measurements = measurements
        self.intents = intents or []
        self.station_status = station_status

    @contextmanager
    def connection(self):
        yield FakeConnection(self)


def measurement(
    station_id: str,
    measured_at: datetime,
    *,
    pm25: float = 60,
    co2: float | None = 900,
    quality_flag: str = "valid",
) -> dict:
    return {
        "station_id": station_id,
        "measured_at": measured_at,
        "pm25": pm25,
        "co2": co2,
        "quality_flag": quality_flag,
    }


def continuous_rows(
    now: datetime,
    *,
    minutes: int,
    pm25: float = 60,
    co2: float | None = 900,
) -> list[dict]:
    return [
        measurement("S03", now - timedelta(minutes=minutes) + timedelta(seconds=60 * index), pm25=pm25, co2=co2)
        for index in range(minutes + 1)
    ]


def test_configured_thirty_second_trigger_requires_full_continuous_window() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    eligible_rows = [
        measurement("S03", now - timedelta(seconds=30)),
        measurement("S03", now - timedelta(seconds=20)),
        measurement("S03", now - timedelta(seconds=10)),
        measurement("S03", now),
    ]
    short_rows = eligible_rows[1:]

    eligible = VentilationService(
        FakeDatabase(eligible_rows),
        trigger_duration_seconds=30,
        max_gap_seconds=15,
    ).assess_trigger("S03", reference_at=now)
    too_short = VentilationService(
        FakeDatabase(short_rows),
        trigger_duration_seconds=30,
        max_gap_seconds=15,
    ).assess_trigger("S03", reference_at=now)

    assert eligible.eligible is True
    assert eligible.required_duration_seconds == 30
    assert too_short.eligible is False


def test_demo_override_qualifies_after_thirty_seconds_without_fabricating_db_history() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    override = {
        "pm25": 120.0,
        "co2": 1600.0,
        "started_at": now - timedelta(seconds=30),
        "source": "demo_override",
    }
    service = VentilationService(
        FakeDatabase([]),
        trigger_duration_seconds=30,
        demo_override_provider=lambda station_id: override if station_id == "S03" else None,
        clock=lambda: now,
    )

    result = service.assess_trigger("S03", reference_at=now)

    assert result.eligible is True
    assert result.continuous_duration_seconds == 30
    assert result.triggered_metrics == ("pm25", "co2")
    assert result.evidence_source == "demo_override"


def test_demo_override_does_not_qualify_before_thirty_seconds() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    service = VentilationService(
        FakeDatabase([]),
        trigger_duration_seconds=30,
        demo_override_provider=lambda _station_id: {
            "pm25": 120.0,
            "co2": 1600.0,
            "started_at": now - timedelta(seconds=20),
            "source": "demo_override",
        },
    )

    result = service.assess_trigger("S03", reference_at=now)

    assert result.eligible is False
    assert result.reason_code == "continuous_window_too_short"
    assert result.continuous_duration_seconds == 20


def test_alert_gate_accepts_only_matching_metrics_from_qualified_demo_override() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    db = FakeDatabase([])
    policy = VentilationService(
        db,
        trigger_duration_seconds=30,
        demo_override_provider=lambda _station_id: {
            "pm25": 120.0,
            "co2": 900.0,
            "started_at": now - timedelta(seconds=30),
            "source": "demo_override",
        },
        clock=lambda: now,
    )
    engine = AlertEngine(
        db=db,
        station_service=object(),
        audit=object(),
        warning_threshold=50,
        critical_threshold=100,
        rule_version="pm25-threshold-v1",
        ventilation_service=policy,
    )

    pm25_rule = next(rule for rule in engine.rules if rule.alert_type == "pm25_threshold")
    co2_rule = next(rule for rule in engine.rules if rule.alert_type == "co2_threshold")

    assert engine._rule_threshold_is_qualified("S03", pm25_rule) is True
    assert engine._rule_threshold_is_qualified("S03", co2_rule) is False


def test_trigger_requires_strict_threshold_for_full_fifteen_minutes() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    at_boundary = continuous_rows(now, minutes=15, pm25=50, co2=1000)
    service = VentilationService(FakeDatabase(at_boundary), max_gap_seconds=60)

    result = service.assess_trigger("S03", reference_at=now)

    assert result.eligible is False


def test_pm25_or_co2_continuous_fifteen_minutes_is_eligible() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    pm25_service = VentilationService(
        FakeDatabase(continuous_rows(now, minutes=15, pm25=50.1, co2=900)),
        max_gap_seconds=60,
    )
    co2_service = VentilationService(
        FakeDatabase(continuous_rows(now, minutes=15, pm25=20, co2=1000.1)),
        max_gap_seconds=60,
    )

    pm25_result = pm25_service.assess_trigger("S03", reference_at=now)
    co2_result = co2_service.assess_trigger("S03", reference_at=now)

    assert pm25_result.eligible is True
    assert pm25_result.triggered_metrics == ("pm25",)
    assert co2_result.eligible is True
    assert co2_result.triggered_metrics == ("co2",)


def test_short_window_gap_or_invalid_sample_blocks_trigger() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    short_rows = continuous_rows(now, minutes=14)
    gap_rows = continuous_rows(now, minutes=15)
    del gap_rows[8]
    invalid_rows = continuous_rows(now, minutes=15)
    invalid_rows[8]["quality_flag"] = "invalid"

    assert VentilationService(FakeDatabase(short_rows), max_gap_seconds=60).assess_trigger(
        "S03", reference_at=now
    ).eligible is False
    assert VentilationService(FakeDatabase(gap_rows), max_gap_seconds=60).assess_trigger(
        "S03", reference_at=now
    ).eligible is False
    assert VentilationService(FakeDatabase(invalid_rows), max_gap_seconds=60).assess_trigger(
        "S03", reference_at=now
    ).eligible is False


def test_offline_station_blocks_trigger_and_recovery_even_with_fresh_valid_measurements() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    rows = continuous_rows(now, minutes=20, pm25=60, co2=1100)
    intent = {
        "command_intent_id": "intent-001",
        "device_id": "FILTER-01",
        "station_id": "S03",
        "command": "ventilation_boost",
        "status": "succeeded",
        "created_at": now - timedelta(minutes=30),
        "dispatched_at": now - timedelta(minutes=30),
        "ack_status": "succeeded",
        "acknowledged_at": now - timedelta(minutes=30),
    }
    service = VentilationService(
        FakeDatabase(rows, [intent], station_status="offline"),
        max_gap_seconds=60,
    )

    trigger = service.assess_trigger("S03", reference_at=now)
    recovery = service.assess_recovery("S03", reference_at=now)

    assert trigger.eligible is False and trigger.reason_code == "station_offline"
    assert recovery.eligible is False and recovery.reason_code == "station_offline"


def test_safe_recovery_requires_succeeded_boost_and_twenty_continuous_minutes() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    rows = continuous_rows(now, minutes=20, pm25=24.9, co2=699)
    intent = {
        "command_intent_id": "intent-001",
        "device_id": "FILTER-01",
        "station_id": "S03",
        "command": "ventilation_boost",
        "status": "succeeded",
        "created_at": now - timedelta(minutes=30),
        "dispatched_at": now - timedelta(minutes=30),
        "ack_status": "succeeded",
        "acknowledged_at": now - timedelta(minutes=30),
    }
    result = VentilationService(
        FakeDatabase(rows, [intent]),
        max_gap_seconds=60,
    ).assess_recovery("S03", reference_at=now)

    assert result.eligible is True
    assert result.source_command_intent_id == "intent-001"
    assert result.device_id == "FILTER-01"


def test_safe_recovery_requires_correlated_succeeded_acknowledgement() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    rows = continuous_rows(now, minutes=20, pm25=24.9, co2=699)
    intent = {
        "command_intent_id": "intent-without-ack",
        "device_id": "FILTER-01",
        "station_id": "S03",
        "command": "ventilation_boost",
        "status": "succeeded",
        "created_at": now - timedelta(minutes=30),
        "dispatched_at": now - timedelta(minutes=30),
        "ack_status": None,
        "acknowledged_at": None,
    }

    result = VentilationService(
        FakeDatabase(rows, [intent]),
        max_gap_seconds=60,
    ).assess_recovery("S03", reference_at=now)

    assert result.eligible is False
    assert result.reason_code == "boost_acknowledgement_missing"
    assert result.source_command_intent_id == "intent-without-ack"


def test_safe_recovery_uses_strict_pm25_and_co2_thresholds() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    intent = {
        "command_intent_id": "intent-boundary",
        "device_id": "FILTER-01",
        "station_id": "S03",
        "command": "ventilation_boost",
        "status": "succeeded",
        "created_at": now - timedelta(minutes=30),
        "dispatched_at": now - timedelta(minutes=30),
        "ack_status": "succeeded",
        "acknowledged_at": now - timedelta(minutes=30),
    }

    pm25_boundary = VentilationService(
        FakeDatabase(continuous_rows(now, minutes=20, pm25=25, co2=699), [intent]),
        max_gap_seconds=60,
    ).assess_recovery("S03", reference_at=now)
    co2_boundary = VentilationService(
        FakeDatabase(continuous_rows(now, minutes=20, pm25=24.9, co2=700), [intent]),
        max_gap_seconds=60,
    ).assess_recovery("S03", reference_at=now)

    assert pm25_boundary.eligible is False
    assert pm25_boundary.reason_code == "safe_values_not_continuous"
    assert co2_boundary.eligible is False
    assert co2_boundary.reason_code == "safe_values_not_continuous"


def test_recovery_missing_co2_or_without_succeeded_boost_is_blocked() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    rows = continuous_rows(now, minutes=20, pm25=20, co2=None)
    intent = {
        "command_intent_id": "intent-001",
        "device_id": "FILTER-01",
        "station_id": "S03",
        "command": "ventilation_boost",
        "status": "succeeded",
        "created_at": now - timedelta(minutes=30),
        "dispatched_at": now - timedelta(minutes=30),
        "ack_status": "succeeded",
        "acknowledged_at": now - timedelta(minutes=30),
    }

    missing_co2 = VentilationService(FakeDatabase(rows, [intent]), max_gap_seconds=60).assess_recovery(
        "S03", reference_at=now
    )
    no_boost = VentilationService(FakeDatabase(rows), max_gap_seconds=60).assess_recovery(
        "S03", reference_at=now
    )

    assert missing_co2.eligible is False
    assert no_boost.reason_code == "no_succeeded_boost"


def test_active_alert_response_is_enriched_with_grounded_ventilation_context() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    db = FakeDatabase(continuous_rows(now, minutes=15, pm25=60, co2=900))
    policy = VentilationService(db, max_gap_seconds=60, clock=lambda: now)
    engine = AlertEngine(
        db=db,
        station_service=object(),
        audit=object(),
        warning_threshold=50,
        critical_threshold=100,
        rule_version="pm25-threshold-v1",
        ventilation_service=policy,
    )

    enriched = engine._enrich_alert(
        {
            "alert_id": "alert-1",
            "station_id": "S03",
            "alert_type": "pm25_threshold",
            "rule_version": "pm25-threshold-v1",
            "severity": "warning",
            "status": "active",
        }
    )

    assert enriched["ventilation_eligible"] is True
    assert enriched["recommended_action"] == "ventilation_boost"
    assert enriched["recommended_duration_minutes"] == 45
    assert enriched["recommended_intensity_percent"] == 80


def test_alert_store_failure_is_structured_and_never_fabricates_fallback_alerts() -> None:
    class FailingDatabase:
        @contextmanager
        def connection(self):
            raise RuntimeError("database unavailable")
            yield  # pragma: no cover

    engine = AlertEngine(
        db=FailingDatabase(),
        station_service=object(),
        audit=object(),
        warning_threshold=50,
        critical_threshold=100,
        rule_version="pm25-threshold-v1",
    )

    with pytest.raises(ServiceError) as exc_info:
        engine.list_alerts(status="active", station_id="S03")

    assert exc_info.value.code == "alert_store_unavailable"
    assert exc_info.value.status_code == 503


def test_device_proposal_is_rejected_at_service_boundary_before_fifteen_minutes() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    db = FakeDatabase(continuous_rows(now, minutes=14, pm25=60, co2=900))
    policy = VentilationService(db, max_gap_seconds=60, clock=lambda: now)
    service = ApprovalService(db, object(), ventilation_service=policy)

    with pytest.raises(ServiceError) as exc_info:
        service.create_request(
            request_type="warning_proposal",
            station_id="S03",
            device_id=None,
            proposed_action="ventilation_boost",
            reason="Caller-provided evidence must not bypass the backend continuity rule.",
            evidence={"control": {"duration_minutes": 45, "intensity_percent": 80}},
            created_by="ai_agent",
            correlation_id="corr-under-window",
        )

    assert exc_info.value.code == "ventilation_not_eligible"
    assert exc_info.value.status_code == 409


def test_agent_cannot_override_backend_duration_or_intensity_policy() -> None:
    now = datetime(2026, 8, 21, 5, tzinfo=UTC)
    db = FakeDatabase(continuous_rows(now, minutes=15, pm25=60, co2=900))
    policy = VentilationService(db, max_gap_seconds=60, clock=lambda: now)
    service = ApprovalService(db, object(), ventilation_service=policy)

    with pytest.raises(ServiceError) as exc_info:
        service._normalize_device_request(
            FakeCursor(db),
            station_id="S03",
            requested_device_id=None,
            proposed_action="ventilation_boost",
            evidence={"control": {"duration_minutes": 60, "intensity_percent": 80}},
        )

    assert exc_info.value.code == "device_control_policy_mismatch"
