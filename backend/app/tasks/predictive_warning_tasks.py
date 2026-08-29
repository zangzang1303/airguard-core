from __future__ import annotations

import os
from uuid import uuid4

from ..celery_app import celery_app
from ..core import Settings
from ..services.audit_service import AuditService
from ..services.database import Database, ServiceError
from ..services.personalized_alert_repository import PersonalizedAlertRepository
from ..services.predictive_warning_email import render_predictive_warning_email
from ..services.predictive_warning_service import (
    PredictiveWarningNotificationService,
    PredictiveWarningService,
)
from ..services.resend_email_provider import ResendEmailProvider
from ..services.station_service import StationService
from .task_support import RETRY_TASK_OPTIONS, TransientTaskError, run_idempotent


def _services(notification_task=None):
    settings = Settings.load()
    database = Database(os.getenv("DATABASE_URL"))
    audit = AuditService(database)
    repository = PersonalizedAlertRepository(database)
    station_service = StationService(database, settings.stale_after_seconds)
    notifier = PredictiveWarningNotificationService(
        repository,
        audit,
        notification_task=notification_task,
        enabled=settings.predictive_warning_notifications_enabled,
    )
    service = PredictiveWarningService(
        repository,
        station_service,
        audit,
        notifier=notifier,
        policy_version=settings.predictive_warning_policy_version,
        threshold_rule_version=settings.alert_rule_version,
        warning_threshold=settings.alert_warning_threshold,
        critical_threshold=settings.alert_critical_threshold,
        observation_max_age_seconds=settings.stale_after_seconds,
        min_confidence=settings.predictive_warning_min_confidence,
        forecast_max_age_seconds=settings.predictive_warning_forecast_max_age_seconds,
        clear_evaluations=settings.predictive_warning_clear_evaluations,
        lead_minutes=settings.predictive_warning_lead_minutes,
        lead_tolerance_minutes=settings.predictive_warning_lead_tolerance_minutes,
    )
    return settings, repository, audit, service


@celery_app.task(name="airguard.predictive_warning.notify", **RETRY_TASK_OPTIONS)
def send_predictive_warning_notification(
    self,
    episode_id: str,
    recipient_user_id: str,
    idempotency_key: str,
) -> dict:
    task_id = self.request.id

    def operation() -> dict:
        settings, repository, audit, service = _services()
        try:
            episode, recipient = service.revalidate_for_delivery(episode_id, recipient_user_id)
        except ServiceError as exc:
            audit.record(
                actor_type="system",
                actor_role="worker",
                action="predictive_warning.notification.cancelled",
                entity_type="predictive_warning_episode",
                entity_id=episode_id,
                correlation_id=task_id,
                outcome="cancelled",
                details={"recipient_user_id": recipient_user_id, "reason_code": exc.code},
            )
            return {
                "task_id": task_id,
                "job_type": "predictive_warning_notification",
                "delivery_status": "cancelled",
                "reason": exc.code,
            }
        rendered = render_predictive_warning_email(episode, frontend_url=settings.frontend_url)
        result = ResendEmailProvider().send(
            recipient=recipient["email"],
            subject=rendered["subject"],
            text=rendered["text"],
            html=rendered["html"],
            email_type="predictive_warning",
            idempotency_key=idempotency_key,
        )
        if result.retryable:
            raise TransientTaskError(f"predictive warning provider failure: {result.reason_code}")
        if result.status == "accepted":
            repository.mark_notified(episode_id)
            audit.record(
                actor_type="system",
                actor_role="worker",
                action="predictive_warning.notification.accepted",
                entity_type="predictive_warning_episode",
                entity_id=episode_id,
                correlation_id=task_id,
                details={"recipient_user_id": recipient_user_id, "provider": "resend"},
            )
        else:
            audit.record(
                actor_type="system",
                actor_role="worker",
                action="predictive_warning.notification.failure" if result.status == "failed" else "predictive_warning.notification.skipped",
                entity_type="predictive_warning_episode",
                entity_id=episode_id,
                correlation_id=task_id,
                outcome="failure" if result.status == "failed" else "skipped",
                details={
                    "recipient_user_id": recipient_user_id,
                    "provider": result.provider,
                    "reason_code": result.reason_code,
                },
            )
        return {
            "task_id": task_id,
            "job_type": "predictive_warning_notification",
            "delivery_status": result.status,
            "provider": result.provider,
            "provider_message_id": result.provider_message_id,
            "reason": result.reason_code,
        }

    return run_idempotent(task_id=task_id, idempotency_key=idempotency_key, operation=operation)


@celery_app.task(name="airguard.predictive_warning.evaluate", **RETRY_TASK_OPTIONS)
def evaluate_predictive_warnings(self, station_id: str | None = None) -> dict:
    _settings, _repository, audit, service = _services(send_predictive_warning_notification)
    station_ids = [station_id] if station_id else ["S01", "S02", "S03", "S04", "S05"]
    results = []
    for current_station_id in station_ids:
        correlation_id = f"predictive-eval:{self.request.id or uuid4()}:{current_station_id}"
        try:
            results.append(
                {
                    "station_id": current_station_id,
                    **service.evaluate(current_station_id, dry_run=False, correlation_id=correlation_id),
                }
            )
        except ServiceError as exc:
            audit.record(
                actor_type="system",
                actor_role="worker",
                action="predictive_warning.evaluation.failure",
                entity_type="station",
                entity_id=current_station_id,
                correlation_id=correlation_id,
                outcome="failure",
                details={"reason_code": exc.code},
            )
            results.append({"station_id": current_station_id, "outcome": "failed", "reason_code": exc.code})
    return {"task_id": self.request.id, "results": results}
