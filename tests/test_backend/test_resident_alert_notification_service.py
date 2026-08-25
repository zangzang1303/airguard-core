from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.services.alert_engine import AlertEngine
from backend.app.services.resident_alert_notification_service import (
    RESIDENT_ALERT_POLICY_VERSION,
    ResidentAlertNotificationService,
)


class FakeUserService:
    def __init__(self, recipients: list[dict[str, str]]) -> None:
        self.recipients = recipients

    def list_resident_alert_recipients(self) -> list[dict[str, str]]:
        return self.recipients


class FailingUserService:
    def list_resident_alert_recipients(self) -> list[dict[str, str]]:
        raise ConnectionError("database unavailable")


class FakeAuditService:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def record(self, **kwargs: Any) -> dict[str, int]:
        self.records.append(kwargs)
        return {"audit_id": len(self.records)}


class FakeNotificationTask:
    def __init__(self, failure: Exception | None = None) -> None:
        self.failure = failure
        self.calls: list[dict[str, Any]] = []

    def apply_async(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        if self.failure:
            raise self.failure


class FakeJobStore:
    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}
        self.failed: list[dict[str, Any]] = []

    def reserve(
        self,
        task_id: str,
        job_type: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        if idempotency_key in self.jobs:
            return self.jobs[idempotency_key], False
        job = {
            "task_id": task_id,
            "job_type": job_type,
            "idempotency_key": idempotency_key,
            "status": "PENDING",
            "request": payload,
        }
        self.jobs[idempotency_key] = job
        return job, True

    def mark_failed(self, task_id: str, error: str, *, retrying: bool) -> None:
        self.failed.append({"task_id": task_id, "error": error, "retrying": retrying})


def active_alert(**overrides: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "alert_id": "alert-001",
        "station_id": "S03",
        "alert_type": "pm25_threshold",
        "status": "active",
        "severity": "warning",
        "metric": "pm25",
        "observed_value": 55.0,
        "threshold_value": 50.0,
        "title": "PM2.5 vượt ngưỡng tại S03",
    }
    result.update(overrides)
    return result


def build_service(
    recipients: list[dict[str, str]],
    *,
    task: FakeNotificationTask | None = None,
    audit: FakeAuditService | None = None,
    jobs: FakeJobStore | None = None,
) -> tuple[ResidentAlertNotificationService, FakeNotificationTask, FakeAuditService, FakeJobStore]:
    task = task or FakeNotificationTask()
    audit = audit or FakeAuditService()
    jobs = jobs or FakeJobStore()
    service = ResidentAlertNotificationService(
        user_service=FakeUserService(recipients),  # type: ignore[arg-type]
        audit_service=audit,  # type: ignore[arg-type]
        notification_task=task,
        clock=lambda: datetime(2026, 8, 24, 12, 30, tzinfo=UTC),
        reserve_job_fn=jobs.reserve,
        mark_job_failed_fn=jobs.mark_failed,
    )
    return service, task, audit, jobs


def test_queues_one_personalized_notification_for_every_resident_group() -> None:
    recipients = [
        {"user_id": "resident-normal", "email": "normal@example.com", "sensitivity_group": "normal"},
        {"user_id": "resident-sensitive", "email": "sensitive@example.com", "sensitivity_group": "sensitive"},
        {"user_id": "resident-outdoor", "email": "outdoor@example.com", "sensitivity_group": "outdoor_sport"},
    ]
    service, task, audit, jobs = build_service(recipients)

    result = service.notify(alert=active_alert(), correlation_id="corr-001")

    assert result == {"enqueued": 3, "reused": 0, "failed": 0}
    assert len(task.calls) == 3
    messages = [call["kwargs"]["message"] for call in task.calls]
    assert any("Ưu tiên ở trong nhà" in message for message in messages)
    assert any("vận động ngoài trời" in message for message in messages)
    assert all("simulator" in message for message in messages)
    assert all(call["kwargs"]["email_type"] == "resident_environmental_alert" for call in task.calls)
    assert all(job["job_type"] == "resident_alert_notification" for job in jobs.jobs.values())
    assert len(audit.records) == 3
    assert all(record["action"] == "alert.notification.enqueued" for record in audit.records)
    assert all(record["details"]["policy_version"] == RESIDENT_ALERT_POLICY_VERSION for record in audit.records)
    assert not any("email" in str(record).lower() or "@" in str(record) for record in audit.records)


def test_same_alert_and_severity_is_idempotent_but_escalation_is_sent_once() -> None:
    recipients = [
        {"user_id": "resident-1", "email": "resident@example.com", "sensitivity_group": "normal"},
    ]
    service, task, _, _ = build_service(recipients)

    first = service.notify(alert=active_alert(), correlation_id="corr-first")
    duplicate = service.notify(alert=active_alert(observed_value=60.0), correlation_id="corr-repeat")
    escalated = service.notify(
        alert=active_alert(severity="critical", observed_value=120.0),
        correlation_id="corr-critical",
    )

    assert first["enqueued"] == 1
    assert duplicate == {"enqueued": 0, "reused": 1, "failed": 0}
    assert escalated["enqueued"] == 1
    assert len(task.calls) == 2


def test_new_alert_lifecycle_inside_cooldown_does_not_spam_same_resident() -> None:
    recipients = [
        {"user_id": "resident-1", "email": "resident@example.com", "sensitivity_group": "normal"},
    ]
    service, task, _, _ = build_service(recipients)

    first = service.notify(alert=active_alert(alert_id="alert-old"), correlation_id="corr-old")
    reopened = service.notify(alert=active_alert(alert_id="alert-new"), correlation_id="corr-new")

    assert first["enqueued"] == 1
    assert reopened == {"enqueued": 0, "reused": 1, "failed": 0}
    assert len(task.calls) == 1


def test_resolved_and_sensor_offline_alerts_do_not_notify_residents() -> None:
    service, task, _, _ = build_service(
        [{"user_id": "resident-1", "email": "resident@example.com", "sensitivity_group": "sensitive"}]
    )

    assert service.should_notify(active_alert(status="resolved")) is False
    assert service.should_notify(active_alert(alert_type="sensor_offline")) is False
    assert service.notify(alert=active_alert(status="resolved"), correlation_id="corr-resolved")["enqueued"] == 0
    assert task.calls == []


def test_enqueue_failure_is_audited_without_exposing_recipient_email() -> None:
    task = FakeNotificationTask(ConnectionError("broker unavailable"))
    service, _, audit, jobs = build_service(
        [{"user_id": "resident-1", "email": "resident@example.com", "sensitivity_group": "sensitive"}],
        task=task,
    )

    result = service.notify(alert=active_alert(), correlation_id="corr-failure")

    assert result == {"enqueued": 0, "reused": 0, "failed": 1}
    assert len(jobs.failed) == 1
    assert audit.records[-1]["action"] == "alert.notification.failure"
    assert audit.records[-1]["details"]["reason"] == "ConnectionError"
    assert "resident@example.com" not in str(audit.records[-1])


def test_recipient_lookup_failure_is_audited_and_does_not_raise() -> None:
    audit = FakeAuditService()
    service = ResidentAlertNotificationService(
        user_service=FailingUserService(),  # type: ignore[arg-type]
        audit_service=audit,  # type: ignore[arg-type]
        notification_task=FakeNotificationTask(),
    )

    result = service.notify(alert=active_alert(), correlation_id="corr-db-failure")

    assert result == {"enqueued": 0, "reused": 0, "failed": 1}
    assert audit.records[-1]["action"] == "alert.notification.failure"
    assert audit.records[-1]["details"] == {
        "reason": "recipient_lookup_failed",
        "error_type": "ConnectionError",
        "policy_version": RESIDENT_ALERT_POLICY_VERSION,
    }


def test_alert_engine_exposes_all_simultaneous_alerts_for_notifications() -> None:
    class FakeStationService:
        @staticmethod
        def get_station(_station_id: str) -> dict[str, Any]:
            return {"station_id": "S03", "status": "online", "is_stale": False, "pm25": 80.0}

    engine = AlertEngine.__new__(AlertEngine)
    engine.station_service = FakeStationService()  # type: ignore[assignment]
    engine.rules = ("pm25", "co2")  # type: ignore[assignment]
    engine._resolve_sensor_offline = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    engine._evaluate_rule = lambda _station, rule, **_kwargs: {  # type: ignore[method-assign]
        "alert_id": f"alert-{rule}",
        "station_id": "S03",
        "alert_type": f"{rule}_threshold",
        "status": "active",
        "severity": "warning" if rule == "pm25" else "critical",
        "updated_at": 1 if rule == "pm25" else 2,
        "ventilation_eligible": False,
    }
    engine._with_ventilation_context = lambda alert: alert  # type: ignore[method-assign]
    engine._recovery_signal = lambda _station_id: None  # type: ignore[method-assign]

    primary, evaluated = engine.evaluate_station_with_alerts("S03", correlation_id="corr-multi")

    assert primary is not None
    assert primary["alert_id"] == "alert-co2"
    assert {alert["alert_id"] for alert in evaluated} == {"alert-pm25", "alert-co2"}
