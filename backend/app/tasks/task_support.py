from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.services.job_service import get_job, mark_job_failed, mark_job_running, mark_job_succeeded


class TransientTaskError(ConnectionError):
    """Retryable network or temporary infrastructure failure."""


RETRY_TASK_OPTIONS = {
    "bind": True,
    "acks_late": True,
    "autoretry_for": (TransientTaskError,),
    "retry_backoff": True,
    "retry_backoff_max": 60,
    "retry_jitter": True,
    "max_retries": 3,
}


def run_idempotent(
    *,
    task_id: str,
    idempotency_key: str,
    operation: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    existing = get_job(task_id)
    if existing and existing.get("status") == "SUCCESS" and existing.get("result") is not None:
        return existing["result"]

    mark_job_running(task_id)
    try:
        result = operation()
    except TransientTaskError as exc:
        mark_job_failed(task_id, str(exc), retrying=True)
        raise
    except Exception as exc:
        mark_job_failed(task_id, str(exc), retrying=False)
        raise

    result.setdefault("idempotency_key", idempotency_key)
    mark_job_succeeded(task_id, result)
    return result
