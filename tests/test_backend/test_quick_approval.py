from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import UUID

import pytest

from backend.app.services.approval_service import (
    ApprovalService,
    ApprovalStoreUnavailableError,
    stable_device_command_id,
)
from backend.app.services.database import ServiceError
from backend.app.services.ventilation_service import VentilationAssessment


class FakeApprovalDatabase:
    def __init__(self) -> None:
        self.approval = {
            "request_id": UUID("00000000-0000-0000-0000-000000000201"),
            "request_type": "warning_proposal",
            "station_id": "S03",
            "device_id": "FILTER-01",
            "proposed_action": "ventilation_boost",
            "reason": "qualified",
            "evidence": {"control": {"duration_minutes": 45, "intensity_percent": 80}},
            "duration_minutes": 45,
            "intensity_percent": 80,
            "status": "pending",
            "version": 1,
            "review_mode": None,
            "review_idempotency_key": None,
        }
        self.intent: dict | None = None
        self.audit_rows: list[dict] = []
        self.last_dispatch_query: str | None = None

    @contextmanager
    def connection(self):
        yield FakeConnection(self)


class FakeConnection:
    def __init__(self, db: FakeApprovalDatabase) -> None:
        self.db = db

    def cursor(self, **_kwargs):
        return FakeCursor(self.db)


class FakeCursor:
    def __init__(self, db: FakeApprovalDatabase) -> None:
        self.db = db
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, query: str, params=()) -> None:
        normalized = " ".join(query.split())
        if normalized.startswith("SELECT approval_requests.*, audit_logs.audit_id"):
            request_id, key = params
            audit = next(
                (
                    row for row in reversed(self.db.audit_rows)
                    if row["entity_id"] == request_id and row["details"].get("idempotency_key") == key
                ),
                None,
            )
            self.result = {
                **self.db.approval,
                "audit_id": audit["audit_id"],
                "command_intent": self.db.intent,
            } if audit else None
            return
        if normalized.startswith("INSERT INTO users"):
            self.result = None
            return
        if normalized.startswith("UPDATE approval_requests SET status = 'approved'"):
            _reviewer, _note, review_mode, review_key, request_id, expected_version = params
            approval = self.db.approval
            if (
                str(approval["request_id"]) == str(request_id)
                and approval["status"] == "pending"
                and approval["version"] == expected_version
            ):
                approval["status"] = "approved"
                approval["version"] += 1
                approval["review_mode"] = review_mode
                approval["review_idempotency_key"] = review_key
                self.result = dict(approval)
            else:
                self.result = None
            return
        if normalized.startswith("INSERT INTO device_command_intents"):
            intent_id, request_id, device_id, station_id, command, duration, intensity, key = params
            self.db.intent = {
                "command_intent_id": intent_id,
                "approval_request_id": request_id,
                "device_id": device_id,
                "station_id": station_id,
                "command": command,
                "duration_minutes": duration,
                "intensity_percent": intensity,
                "status": "queued",
                "idempotency_key": key,
                "command_id": None,
                "created_at": datetime.now(UTC),
            }
            self.result = dict(self.db.intent)
            return
        if normalized.startswith("SELECT status, version FROM approval_requests"):
            self.result = {
                "status": self.db.approval["status"],
                "version": self.db.approval["version"],
            }
            return
        if normalized.startswith("SELECT device_id FROM devices"):
            self.result = {"device_id": "FILTER-01"}
            return
        if normalized.startswith("UPDATE device_command_intents SET status = CASE"):
            self.db.last_dispatch_query = normalized
            self.result = None
            return
        raise AssertionError(normalized)

    def fetchone(self):
        return self.result


class FakeAudit:
    def __init__(self, db: FakeApprovalDatabase) -> None:
        self.db = db

    def record(self, **kwargs):
        audit_id = len(self.db.audit_rows) + 1
        self.db.audit_rows.append({"audit_id": audit_id, **kwargs})
        return {"audit_id": audit_id}


class EligibleVentilationPolicy:
    def assess_trigger(self, _station_id: str) -> VentilationAssessment:
        return VentilationAssessment(
            eligible=True,
            reason_code="eligible",
            policy_version="test-policy",
            required_duration_seconds=900,
            continuous_duration_seconds=900,
        )


def test_device_command_id_is_stable_across_dispatch_retries() -> None:
    first = stable_device_command_id(
        "00000000-0000-0000-0000-000000000201",
        "FILTER-01",
        "ventilation_boost",
        "approval:201:v2",
    )
    retried = stable_device_command_id(
        "00000000-0000-0000-0000-000000000201",
        "FILTER-01",
        "ventilation_boost",
        "approval:201:v2",
    )

    assert first == retried
    assert str(UUID(first)) == first


def test_mqtt_publish_requires_qos_ack_and_terminal_dispatch_is_not_republished() -> None:
    pytest.importorskip("celery")
    from backend.app.tasks.notification_tasks import (  # noqa: PLC0415
        _close_mqtt_client,
        _dispatch_is_succeeded,
        _wait_for_mqtt_publish,
    )
    from backend.app.tasks.task_support import TransientTaskError  # noqa: PLC0415

    class UnacknowledgedPublish:
        def wait_for_publish(self, *, timeout: float) -> None:
            assert timeout == 5

        def is_published(self) -> bool:
            return False

    with pytest.raises(TransientTaskError):
        _wait_for_mqtt_publish(UnacknowledgedPublish())

    assert _dispatch_is_succeeded({"command_intent_status": "succeeded"}) is True
    assert _dispatch_is_succeeded({"ack_status": "succeeded"}) is True
    assert _dispatch_is_succeeded({"command_intent_status": "published"}) is False

    class FakeClient:
        def __init__(self) -> None:
            self.events: list[str] = []

        def disconnect(self) -> None:
            self.events.append("disconnect")

        def loop_stop(self) -> None:
            self.events.append("loop_stop")

    client = FakeClient()
    _close_mqtt_client(client)
    assert client.events == ["disconnect", "loop_stop"]


def test_dispatch_persistence_and_approval_lookup_translate_database_outage_for_retry() -> None:
    class UnavailableDatabase:
        @contextmanager
        def connection(self):
            raise ServiceError("database_unavailable", "database unavailable", 503)
            yield  # pragma: no cover

    service = ApprovalService(UnavailableDatabase(), object())
    request_id = "00000000-0000-0000-0000-000000000201"

    with pytest.raises(ApprovalStoreUnavailableError):
        service.require_approved_device_action(request_id, "FILTER-01", "ventilation_boost")
    with pytest.raises(ApprovalStoreUnavailableError):
        service.record_device_dispatch(
            request_id=request_id,
            device_id="FILTER-01",
            status="publishing",
            correlation_id="task-1",
            command_id="cmd-1",
        )


def test_dispatch_sql_preserves_terminal_succeeded_intent_on_redelivery() -> None:
    db = FakeApprovalDatabase()
    service = ApprovalService(db, FakeAudit(db))

    service.record_device_dispatch(
        request_id=str(db.approval["request_id"]),
        device_id="FILTER-01",
        status="publishing",
        correlation_id="task-redelivery",
        command_id="cmd-1",
    )

    assert db.last_dispatch_query is not None
    assert "status = 'succeeded' OR ack_status = 'succeeded'" in db.last_dispatch_query


def test_quick_approve_reuses_retry_key_and_creates_exactly_one_intent() -> None:
    db = FakeApprovalDatabase()
    service = ApprovalService(db, FakeAudit(db))
    request_id = str(db.approval["request_id"])
    reviewer_id = "00000000-0000-0000-0000-000000000001"

    first = service.quick_approve(
        request_id=request_id,
        expected_version=1,
        reviewer_id=reviewer_id,
        reviewer_role="manager",
        note="approved",
        correlation_id="corr-1",
        idempotency_key="quick-key-001",
    )
    first_intent_id = first["command_intent"]["command_intent_id"]
    retried = service.quick_approve(
        request_id=request_id,
        expected_version=1,
        reviewer_id=reviewer_id,
        reviewer_role="manager",
        note="approved",
        correlation_id="corr-2",
        idempotency_key="quick-key-001",
    )

    assert first["status"] == "approved"
    assert retried["reused"] is True
    assert retried["command_intent"]["command_intent_id"] == first_intent_id
    assert len([row for row in db.audit_rows if row["action"] == "approval.quick_approve"]) == 1
    audit = next(row for row in db.audit_rows if row["action"] == "approval.quick_approve")
    assert audit["details"]["station_id"] == "S03"
    assert audit["details"]["proposed_action"] == "ventilation_boost"
    assert first["review_mode"] == retried["review_mode"] == "quick"
    assert first["review_idempotency_key"] == retried["review_idempotency_key"] == "quick-key-001"


def test_standard_approval_persists_standard_review_mode_without_retry_key() -> None:
    db = FakeApprovalDatabase()
    service = ApprovalService(db, FakeAudit(db))

    approved = service.approve(
        request_id=str(db.approval["request_id"]),
        expected_version=1,
        reviewer_id="00000000-0000-0000-0000-000000000001",
        reviewer_role="manager",
        note="approved in detail view",
        correlation_id="corr-standard",
    )

    assert approved["review_mode"] == "standard"
    assert approved["review_idempotency_key"] is None


def test_quick_approve_preserves_manager_and_version_guards() -> None:
    db = FakeApprovalDatabase()
    service = ApprovalService(db, FakeAudit(db))
    request_id = str(db.approval["request_id"])

    try:
        service.quick_approve(
            request_id=request_id,
            expected_version=1,
            reviewer_id="00000000-0000-0000-0000-000000000002",
            reviewer_role="resident",
            note=None,
            correlation_id="corr-denied",
            idempotency_key="quick-key-denied",
        )
    except ServiceError as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("resident must not quick-approve")

    try:
        service.quick_approve(
            request_id=request_id,
            expected_version=2,
            reviewer_id="00000000-0000-0000-0000-000000000001",
            reviewer_role="manager",
            note=None,
            correlation_id="corr-stale",
            idempotency_key="quick-key-stale",
        )
    except ServiceError as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("stale version must not quick-approve")


def test_device_action_duration_is_allowlisted_and_bounded() -> None:
    db = FakeApprovalDatabase()
    service = ApprovalService(
        db,
        FakeAudit(db),
        ventilation_service=EligibleVentilationPolicy(),  # type: ignore[arg-type]
    )
    cursor = FakeCursor(db)

    device_id, evidence = service._normalize_device_request(
        cursor,
        station_id="S03",
        requested_device_id=None,
        proposed_action="ventilation_boost",
        evidence={"control": {}},
    )
    assert device_id == "FILTER-01"
    assert evidence["control"]["duration_minutes"] == 45
    assert evidence["control"]["intensity_percent"] == 80

    try:
        service._normalize_device_request(
            cursor,
            station_id="S03",
            requested_device_id=None,
            proposed_action="ventilation_boost",
            evidence={"control": {"duration_minutes": 4, "intensity_percent": 80}},
        )
    except ServiceError as exc:
        assert exc.code == "invalid_duration"
    else:
        raise AssertionError("duration below five minutes must be rejected")
