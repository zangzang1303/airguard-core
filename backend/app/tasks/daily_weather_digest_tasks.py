from __future__ import annotations

import os
from datetime import datetime
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from ..celery_app import celery_app
from ..services.audit_service import AuditService
from ..services.database import Database
from ..services.job_service import mark_job_failed, reserve_job
from ..services.personalized_alert_repository import PersonalizedAlertRepository
from ..services.weather_service import WeatherService
from .notification_tasks import send_notification_job


def _enabled() -> bool:
    return os.getenv("DAILY_WEATHER_DIGEST_NOTIFICATIONS_ENABLED", "false").strip().lower() == "true"


def _render_digest(weather: dict[str, object], date_label: str) -> str:
    source_note = (
        "Nguồn thời tiết đang dùng dữ liệu mô phỏng dự phòng cho MVP."
        if weather.get("is_fallback")
        else "Nguồn thời tiết: Open-Meteo forecast API."
    )
    return (
        f"Bản tin môi trường sáng {date_label} tại Vinhomes Ocean Park 1.\n\n"
        f"Nhiệt độ: {float(weather['temperature']):.1f}°C\n"
        f"Độ ẩm: {float(weather['humidity']):.0f}%\n"
        f"Gió: {float(weather['wind_speed_ms']):.1f} m/s\n"
        f"Mưa: {float(weather['rainfall']):.1f} mm\n\n"
        f"{source_note} Đây là bản tin thông tin cho MVP, không phải cảnh báo chính thức hay tư vấn y tế."
    )


@celery_app.task(name="airguard.weather_digest.send_daily", bind=True)
def send_daily_weather_digest(self) -> dict:
    """Send the 07:00 local weather digest only to verified residents who opted in."""
    if not _enabled():
        return {"task_id": self.request.id, "status": "skipped", "reason": "feature_disabled"}

    timezone_name = os.getenv("REPORT_TIMEZONE", "Asia/Ho_Chi_Minh")
    now = datetime.now(ZoneInfo(timezone_name))
    repository = PersonalizedAlertRepository(Database(os.getenv("DATABASE_URL")))
    audit = AuditService(Database(os.getenv("DATABASE_URL")))
    weather = WeatherService(
        os.getenv("WEATHER_API_BASE_URL", "").strip() or None,
        latitude=float(os.getenv("WEATHER_LATITUDE", "20.993")),
        longitude=float(os.getenv("WEATHER_LONGITUDE", "105.944")),
        timeout_seconds=float(os.getenv("WEATHER_TIMEOUT_SECONDS", "3")),
        max_age_seconds=int(os.getenv("WEATHER_MAX_AGE_SECONDS", "3600")),
    ).current_weather()
    if weather.get("is_stale"):
        audit.record(
            actor_type="system", actor_role="backend", action="weather_digest.notification.skipped",
            entity_type="weather_digest", entity_id=now.date().isoformat(), correlation_id=self.request.id,
            outcome="skipped", details={"reason": "weather_stale", "source": weather["source"]},
        )
        return {"task_id": self.request.id, "status": "skipped", "reason": "weather_stale"}
    message = _render_digest(weather, now.strftime("%d/%m/%Y"))
    recipients = repository.list_daily_weather_digest_recipients()
    enqueued = reused = failed = 0
    for recipient in recipients:
        user_id = str(recipient["user_id"])
        idempotency_key = f"daily-weather-digest:{now.date().isoformat()}:{user_id}"
        task_id = str(uuid5(NAMESPACE_URL, f"airguard:{idempotency_key}"))
        payload = {
            "recipient": recipient["email"],
            "message": message,
            "subject": f"AirGuard — Bản tin thời tiết sáng {now.strftime('%d/%m')}",
            "email_type": "daily_weather_digest",
            "idempotency_key": idempotency_key,
        }
        try:
            job, created = reserve_job(task_id, "daily_weather_digest", idempotency_key, payload)
            if not created and job.get("status") != "FAILURE":
                reused += 1
                continue
            send_notification_job.apply_async(kwargs=payload, task_id=str(job.get("task_id") or task_id))
            enqueued += 1
        except Exception as exc:
            failed += 1
            mark_job_failed(task_id, "daily_weather_digest_enqueue_failed", retrying=False)
            audit.record(
                actor_type="system", actor_role="backend", action="weather_digest.notification.failure",
                entity_type="user", entity_id=user_id, correlation_id=self.request.id, outcome="failure",
                details={"error_type": exc.__class__.__name__},
            )
    audit.record(
        actor_type="system", actor_role="backend", action="weather_digest.notification.completed",
        entity_type="weather_digest", entity_id=now.date().isoformat(), correlation_id=self.request.id,
        details={"enqueued": enqueued, "reused": reused, "failed": failed, "source": weather["source"]},
    )
    return {"task_id": self.request.id, "status": "completed", "enqueued": enqueued, "reused": reused, "failed": failed}
