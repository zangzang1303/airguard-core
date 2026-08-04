from __future__ import annotations

from ..celery_app import celery_app
from ..services.forecast_service import baseline_forecast
from .task_support import RETRY_TASK_OPTIONS, run_idempotent


@celery_app.task(name="airguard.forecast.run", **RETRY_TASK_OPTIONS)
def run_forecast_job(
    self,
    station_id: str,
    current_pm25: float,
    hours: int,
    idempotency_key: str,
) -> dict:
    task_id = self.request.id

    def operation() -> dict:
        return {
            "task_id": task_id,
            "job_type": "forecast",
            "station_id": station_id,
            "items": baseline_forecast(current_pm25, hours),
            "model": "baseline_placeholder",
            "todo": "Replace with a validated forecasting pipeline.",
        }

    return run_idempotent(task_id=task_id, idempotency_key=idempotency_key, operation=operation)
