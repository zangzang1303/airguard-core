from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

import app.main as main_mod  # noqa: E402
from app.dependencies.auth import require_manager  # noqa: E402
from app.tasks.notification_tasks import send_notification_job  # noqa: E402

REPORT_ID = "00000000-0000-0000-0000-000000000301"
APPROVAL_ID = "00000000-0000-0000-0000-000000000201"
MANAGER_ID = "00000000-0000-0000-0000-000000000001"


def test_person_b_privileged_endpoints_require_authentication() -> None:
    main_mod.app.dependency_overrides.clear()
    client = TestClient(main_mod.app)

    requests = (
        client.get("/api/v1/reports"),
        client.get(f"/api/v1/reports/{REPORT_ID}"),
        client.get(f"/api/v1/reports/{REPORT_ID}/export?format=markdown"),
        client.post("/api/v1/reports/generate", json={"type": "daily"}),
        client.post(
            f"/api/v1/approvals/{APPROVAL_ID}/quick-approve",
            json={"version": 1},
            headers={"Idempotency-Key": "quick-api-001"},
        ),
    )

    assert all(response.status_code == 401 for response in requests)
    assert all(response.json()["code"] == "unauthenticated" for response in requests)


def test_credentialed_cors_is_limited_to_configured_origins() -> None:
    client = TestClient(main_mod.app)
    preflight_headers = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-csrf-token,idempotency-key",
    }

    allowed = client.options(
        f"/api/v1/approvals/{APPROVAL_ID}/quick-approve",
        headers={**preflight_headers, "Origin": "http://localhost:5173"},
    )
    rejected = client.options(
        f"/api/v1/approvals/{APPROVAL_ID}/quick-approve",
        headers={**preflight_headers, "Origin": "https://attacker.example"},
    )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert rejected.status_code == 400
    assert "access-control-allow-origin" not in rejected.headers


def test_quick_approve_and_report_generate_reject_invalid_csrf(monkeypatch) -> None:
    async def manager_override() -> dict[str, str]:
        return {"user_id": MANAGER_ID, "role": "manager"}

    class MustNotApprove:
        def quick_approve(self, **_kwargs):
            raise AssertionError("approval service must not run after failed CSRF validation")

    class MustNotGenerate:
        def generate_report(self, *_args, **_kwargs):
            raise AssertionError("report service must not run after failed CSRF validation")

    monkeypatch.setattr(main_mod, "approval_service", MustNotApprove())
    monkeypatch.setattr(main_mod, "report_service", MustNotGenerate())
    main_mod.app.dependency_overrides[require_manager] = manager_override
    try:
        client = TestClient(main_mod.app)
        client.cookies.set("airguard_session", "test-session")
        client.cookies.set("airguard_csrf", "expected-token")
        headers = {"X-CSRF-Token": "wrong-token"}

        quick = client.post(
            f"/api/v1/approvals/{APPROVAL_ID}/quick-approve",
            json={"version": 1},
            headers={**headers, "Idempotency-Key": "quick-api-002"},
        )
        report = client.post(
            "/api/v1/reports/generate",
            json={"type": "weekly"},
            headers=headers,
        )

        assert quick.status_code == 403
        assert quick.json()["code"] == "csrf_validation_failed"
        assert report.status_code == 403
        assert report.json()["code"] == "csrf_validation_failed"
    finally:
        main_mod.app.dependency_overrides.clear()


def test_quick_approve_retry_enqueues_exactly_one_dispatch(monkeypatch) -> None:
    async def manager_override() -> dict[str, str]:
        return {"user_id": MANAGER_ID, "role": "manager"}

    command_intent = {
        "command_intent_id": "00000000-0000-0000-0000-000000000401",
        "device_id": "FILTER-01",
        "command": "ventilation_boost",
        "idempotency_key": "approval-command-001",
        "status": "queued",
    }

    class FakeApprovalService:
        def __init__(self) -> None:
            self.calls = 0

        def quick_approve(self, **_kwargs: Any) -> dict[str, Any]:
            self.calls += 1
            return {
                "request_id": APPROVAL_ID,
                "status": "approved",
                "version": 2,
                "command_intent": command_intent,
                "reused": self.calls > 1,
            }

    class FakeDispatchTask:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def apply_async(self, *, kwargs: dict[str, Any], task_id: str) -> None:
            assert task_id.endswith(command_intent["command_intent_id"])
            self.calls.append(kwargs)

    approval = FakeApprovalService()
    dispatch = FakeDispatchTask()
    jobs: dict[str, dict[str, Any]] = {}

    def reserve_dispatch_job(task_id, job_type, idempotency_key, payload):
        if task_id in jobs:
            return jobs[task_id], False
        jobs[task_id] = {
            "task_id": task_id,
            "job_type": job_type,
            "idempotency_key": idempotency_key,
            "request": payload,
            "status": "PENDING",
        }
        return jobs[task_id], True

    monkeypatch.setattr(main_mod, "approval_service", approval)
    monkeypatch.setattr(main_mod, "publish_approved_device_command", dispatch)
    monkeypatch.setattr(main_mod, "reserve_job", reserve_dispatch_job)
    main_mod.app.dependency_overrides[require_manager] = manager_override
    try:
        client = TestClient(main_mod.app)
        client.cookies.set("airguard_session", "test-session")
        client.cookies.set("airguard_csrf", "csrf-token")
        headers = {
            "X-CSRF-Token": "csrf-token",
            "Idempotency-Key": "quick-api-retry-001",
        }

        first = client.post(
            f"/api/v1/approvals/{APPROVAL_ID}/quick-approve",
            json={"version": 1},
            headers=headers,
        )
        retried = client.post(
            f"/api/v1/approvals/{APPROVAL_ID}/quick-approve",
            json={"version": 1},
            headers=headers,
        )

        assert first.status_code == 200
        assert retried.status_code == 200
        assert retried.json()["reused"] is True
        assert len(dispatch.calls) == 1
        assert dispatch.calls[0]["command"] == "ventilation_boost"
    finally:
        main_mod.app.dependency_overrides.clear()


def test_quick_approve_retry_recovers_after_broker_enqueue_failure(monkeypatch) -> None:
    async def manager_override() -> dict[str, str]:
        return {"user_id": MANAGER_ID, "role": "manager"}

    intent = {
        "command_intent_id": "00000000-0000-0000-0000-000000000402",
        "device_id": "FILTER-01",
        "command": "ventilation_boost",
        "idempotency_key": "approval-command-002",
        "status": "queued",
    }

    class FakeApprovalService:
        def __init__(self) -> None:
            self.calls = 0

        def quick_approve(self, **_kwargs: Any) -> dict[str, Any]:
            self.calls += 1
            return {
                "request_id": APPROVAL_ID,
                "status": "approved",
                "version": 2,
                "command_intent": intent,
                "reused": self.calls > 1,
            }

    class FlakyDispatchTask:
        def __init__(self) -> None:
            self.attempts = 0
            self.successful_payloads: list[dict[str, Any]] = []

        def apply_async(self, *, kwargs: dict[str, Any], task_id: str) -> None:
            self.attempts += 1
            if self.attempts == 1:
                raise ConnectionError("broker unavailable")
            assert task_id.endswith(intent["command_intent_id"])
            self.successful_payloads.append(kwargs)

    class FakeAudit:
        def __init__(self) -> None:
            self.rows: list[dict[str, Any]] = []

        def record(self, **kwargs: Any) -> None:
            self.rows.append(kwargs)

    jobs: dict[str, dict[str, Any]] = {}

    def reserve_dispatch_job(task_id, job_type, idempotency_key, payload):
        if task_id in jobs:
            return jobs[task_id], False
        jobs[task_id] = {
            "task_id": task_id,
            "job_type": job_type,
            "idempotency_key": idempotency_key,
            "request": payload,
            "status": "PENDING",
        }
        return jobs[task_id], True

    def mark_dispatch_failed(task_id, _error, *, retrying):
        assert retrying is False
        jobs[task_id]["status"] = "FAILURE"

    approval = FakeApprovalService()
    dispatch = FlakyDispatchTask()
    audit = FakeAudit()
    monkeypatch.setattr(main_mod, "approval_service", approval)
    monkeypatch.setattr(main_mod, "publish_approved_device_command", dispatch)
    monkeypatch.setattr(main_mod, "audit_service", audit)
    monkeypatch.setattr(main_mod, "reserve_job", reserve_dispatch_job)
    monkeypatch.setattr(main_mod, "mark_job_failed", mark_dispatch_failed)
    main_mod.app.dependency_overrides[require_manager] = manager_override
    try:
        client = TestClient(main_mod.app)
        client.cookies.set("airguard_session", "test-session")
        client.cookies.set("airguard_csrf", "csrf-token")
        headers = {
            "X-CSRF-Token": "csrf-token",
            "Idempotency-Key": "quick-api-retry-002",
        }

        first = client.post(
            f"/api/v1/approvals/{APPROVAL_ID}/quick-approve",
            json={"version": 1},
            headers=headers,
        )
        retried = client.post(
            f"/api/v1/approvals/{APPROVAL_ID}/quick-approve",
            json={"version": 1},
            headers=headers,
        )

        assert first.status_code == retried.status_code == 200
        assert dispatch.attempts == 2
        assert len(dispatch.successful_payloads) == 1
        assert dispatch.successful_payloads[0]["idempotency_key"] == intent["idempotency_key"]
        assert audit.rows[0]["action"] == "approval.dispatch.failure"
    finally:
        main_mod.app.dependency_overrides.clear()


def test_manager_proposal_notification_is_idempotent_and_audit_omits_email(monkeypatch) -> None:
    class FakeUserService:
        @staticmethod
        def list_manager_notification_recipients() -> list[dict[str, str]]:
            return [{"user_id": MANAGER_ID, "email": "manager@example.test"}]

    class FakeNotificationTask:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def apply_async(self, *, kwargs: dict[str, Any], task_id: str) -> None:
            self.calls.append({"kwargs": kwargs, "task_id": task_id})

    class FakeAudit:
        def __init__(self) -> None:
            self.rows: list[dict[str, Any]] = []

        def record(self, **kwargs: Any) -> None:
            self.rows.append(kwargs)

    jobs: dict[str, dict[str, Any]] = {}

    def reserve_notification_job(task_id, job_type, idempotency_key, payload):
        index = f"{job_type}:{idempotency_key}"
        if index in jobs:
            return jobs[index], False
        jobs[index] = {
            "task_id": task_id,
            "job_type": job_type,
            "idempotency_key": idempotency_key,
            "request": payload,
            "status": "PENDING",
        }
        return jobs[index], True

    notification = FakeNotificationTask()
    audit = FakeAudit()
    monkeypatch.setattr(main_mod, "user_service", FakeUserService())
    monkeypatch.setattr(main_mod, "send_notification_job", notification)
    monkeypatch.setattr(main_mod, "audit_service", audit)
    monkeypatch.setattr(main_mod, "reserve_job", reserve_notification_job)

    notification_args = {
        "proposal_id": APPROVAL_ID,
        "station_id": "S03",
        "proposed_action": "ventilation_boost",
        "correlation_id": "proposal-correlation-001",
    }
    main_mod._enqueue_manager_proposal_notification(**notification_args)
    main_mod._enqueue_manager_proposal_notification(**notification_args)

    assert len(notification.calls) == 1
    assert notification.calls[0]["kwargs"]["recipient"] == "manager@example.test"
    assert notification.calls[0]["kwargs"]["idempotency_key"].startswith("proposal-notification:")
    assert [row["action"] for row in audit.rows] == ["proposal.notification.enqueued"]
    assert audit.rows[0]["details"] == {"recipient_user_id": MANAGER_ID}


def test_notification_result_omits_recipient_and_message_from_worker_logs(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATION_PROVIDER", "disabled")

    result = send_notification_job.apply(
        kwargs={
            "recipient": "manager@example.test",
            "message": "Sensitive notification body",
            "idempotency_key": "notification-log-redaction-001",
        },
        task_id="notification-log-redaction-001",
    ).get()

    assert result["delivery_status"] == "not_configured"
    assert "recipient" not in result
    assert "message" not in result
