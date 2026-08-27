from __future__ import annotations

import os

from celery import Celery


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
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    timezone="UTC",
    task_track_started=True,
    task_always_eager=env_bool("CELERY_TASK_ALWAYS_EAGER", True),
    task_eager_propagates=True,
    task_store_eager_result=False,
    broker_connection_retry_on_startup=True,
    result_expires=int(os.getenv("CELERY_RESULT_EXPIRES", "3600")),
    worker_prefetch_multiplier=1,
)
