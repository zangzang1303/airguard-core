from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from ..celery_app import celery_app
from ..services.database import Database, ServiceError
from ..services.report_generator_service import DEFAULT_REPORT_TIMEZONE, ReportGeneratorService
from ..services.report_narrative_service import HttpReportNarrator
from ..services.report_repository import DEFAULT_REPORT_LEASE_SECONDS, PostgresReportRepository
from .task_support import RETRY_TASK_OPTIONS, TransientTaskError


def build_report_service_from_environment() -> ReportGeneratorService:
    repository = PostgresReportRepository(
        Database(os.getenv("DATABASE_URL")),
        lease_seconds=_report_lease_seconds(),
    )
    narrative_url = (os.getenv("REPORT_NARRATIVE_ENDPOINT") or "").strip()
    narrator = None
    if narrative_url:
        try:
            timeout_seconds = float(os.getenv("REPORT_NARRATIVE_TIMEOUT_SECONDS", "5"))
        except (TypeError, ValueError) as exc:
            raise ServiceError(
                "invalid_report_narrative_timeout",
                "REPORT_NARRATIVE_TIMEOUT_SECONDS must be a number.",
                500,
            ) from exc
        if timeout_seconds <= 0:
            raise ServiceError(
                "invalid_report_narrative_timeout",
                "REPORT_NARRATIVE_TIMEOUT_SECONDS must be positive.",
                500,
            )
        narrator = HttpReportNarrator(
            narrative_url,
            timeout_seconds=timeout_seconds,
            service_token=os.getenv("REPORT_NARRATIVE_SERVICE_TOKEN"),
        )
    return ReportGeneratorService(repository, narrator=narrator)


def _report_lease_seconds() -> int:
    raw_value = os.getenv("REPORT_GENERATION_LEASE_SECONDS", str(DEFAULT_REPORT_LEASE_SECONDS))
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ServiceError(
            "invalid_report_generation_lease",
            "REPORT_GENERATION_LEASE_SECONDS must be an integer.",
            500,
        ) from exc
    if value < 1 or value > 3600:
        raise ServiceError(
            "invalid_report_generation_lease",
            "REPORT_GENERATION_LEASE_SECONDS must be between 1 and 3600.",
            500,
        )
    return value


@celery_app.task(name="airguard.report.generate", **RETRY_TASK_OPTIONS)
def generate_environmental_report_job(
    self,
    report_type: str,
    timezone_name: str = DEFAULT_REPORT_TIMEZONE,
    period_start: str | None = None,
    period_end: str | None = None,
    generated_by: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Generate one persisted report.

    Celery/Beat retries are safe because the database unique range is the final
    idempotency authority. ``idempotency_key`` is accepted for compatibility with
    the existing job dispatcher but is never used as environmental evidence.
    """

    del idempotency_key
    try:
        service = build_report_service_from_environment()
        report = service.generate_report(
            report_type,
            period_start=_optional_datetime(period_start),
            period_end=_optional_datetime(period_end),
            timezone_name=timezone_name,
            generated_by=generated_by,
        )
        return _json_safe(report)
    except ServiceError as exc:
        if exc.code == "report_generation_in_progress":
            details = exc.details or {}
            retry_after_seconds = details.get("retry_after_seconds", 1)
            try:
                countdown = max(1, min(int(retry_after_seconds), 3600))
            except (TypeError, ValueError):
                countdown = 1
            raise self.retry(
                exc=TransientTaskError(exc.code),
                countdown=countdown,
            ) from exc
        if exc.status_code >= 500:
            raise TransientTaskError(exc.code) from exc
        raise


def _optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ServiceError("invalid_report_period", "Report task timestamps must be ISO-8601.", 422) from exc


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
