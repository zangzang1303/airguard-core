from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


celery_app = Celery(
    "airguard",
    broker=os.getenv("CELERY_BROKER_URL", "memory://"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "cache+memory://"),
    include=[
        "app.tasks.agent_tasks",
        "app.tasks.forecast_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.daily_weather_digest_tasks",
        "app.tasks.predictive_warning_tasks",
        "app.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    timezone=os.getenv("REPORT_TIMEZONE", "Asia/Ho_Chi_Minh"),
    task_track_started=True,
    task_always_eager=env_bool("CELERY_TASK_ALWAYS_EAGER", True),
    task_eager_propagates=True,
    task_store_eager_result=False,
    broker_connection_retry_on_startup=True,
    result_expires=int(os.getenv("CELERY_RESULT_EXPIRES", "3600")),
    worker_prefetch_multiplier=1,
    beat_schedule={
        "airguard-predictive-warning-evaluate": {
            "task": "airguard.predictive_warning.evaluate",
            "schedule": float(os.getenv("PREDICTIVE_WARNING_EVALUATION_INTERVAL_SECONDS", "900")),
        },
        "airguard-daily-environmental-report": {
            "task": "airguard.report.generate",
            "schedule": crontab(hour=0, minute=10),
            "kwargs": {
                "report_type": "daily",
                "timezone_name": os.getenv("REPORT_TIMEZONE", "Asia/Ho_Chi_Minh"),
            },
        },
        "airguard-weekly-environmental-report": {
            "task": "airguard.report.generate",
            "schedule": crontab(hour=0, minute=20, day_of_week="monday"),
            "kwargs": {
                "report_type": "weekly",
                "timezone_name": os.getenv("REPORT_TIMEZONE", "Asia/Ho_Chi_Minh"),
            },
        },
        "airguard-daily-weather-digest": {
            "task": "airguard.weather_digest.send_daily",
            "schedule": crontab(hour=7, minute=0),
        },
    },
)
