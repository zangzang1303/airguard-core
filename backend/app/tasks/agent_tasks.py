from __future__ import annotations

from ..celery_app import celery_app
from ..core import Settings
from ..services.agent_service import AgentService
from .task_support import RETRY_TASK_OPTIONS, run_idempotent


@celery_app.task(name="airguard.agent.run", **RETRY_TASK_OPTIONS)
def run_agent_job(
    self,
    user_id: str,
    message: str,
    idempotency_key: str,
    station_id: str | None = None,
) -> dict:
    task_id = self.request.id
    settings = Settings.load()
    service = AgentService(settings.agent_service_url, timeout_seconds=settings.agent_service_timeout_seconds)

    def operation() -> dict:
        return {
            "task_id": task_id,
            "job_type": "agent",
            "user_id": user_id,
            **service.chat_sync(
                message=message,
                user_id=user_id,
                station_id=station_id,
                request_id=task_id,
            ),
        }

    return run_idempotent(task_id=task_id, idempotency_key=idempotency_key, operation=operation)
