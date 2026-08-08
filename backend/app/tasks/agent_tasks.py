from __future__ import annotations

from ..celery_app import celery_app
from ..services.agent_service import build_placeholder_answer
from .task_support import RETRY_TASK_OPTIONS, run_idempotent

@celery_app.task(name="airguard.agent.run", **RETRY_TASK_OPTIONS)
def run_agent_job(self, user_id: str, message: str, idempotency_key: str) -> dict:
    task_id = self.request.id

    def operation() -> dict:
        return {
            "task_id": task_id,
            "job_type": "agent",
            "user_id": user_id,
            **build_placeholder_answer(message),
        }

    return run_idempotent(task_id=task_id, idempotency_key=idempotency_key, operation=operation)
