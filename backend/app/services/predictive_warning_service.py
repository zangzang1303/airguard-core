from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .database import ServiceError
from .forecast_service import InsufficientForecastHistory, trend_forecast
from .job_service import mark_job_failed, reserve_job

PREDICTIVE_WARNING_DISCLAIMER = (
    "Cảnh báo dự báo advisory từ dữ liệu simulator và mô hình baseline; "
    "không phải quan trắc chính thức hoặc tư vấn y tế."
)


class PredictiveWarningNotificationService:
    def __init__(
        self,
        repository: Any,
        audit_service: Any,
        *,
        notification_task: Any | None,
        enabled: bool,
        reserve_job_fn: Any = reserve_job,
        mark_job_failed_fn: Any = mark_job_failed,
    ) -> None:
        self.repository = repository
        self.audit = audit_service
        self.notification_task = notification_task
        self.enabled = enabled
        self._reserve_job = reserve_job_fn
        self._mark_job_failed = mark_job_failed_fn

    def enqueue(self, episode: dict[str, Any], correlation_id: str) -> dict[str, int | str]:
        if not self.enabled:
            return {"enqueued": 0, "reused": 0, "failed": 0, "reason_code": "feature_disabled"}
        if self.notification_task is None:
            raise ServiceError("scheduler_unavailable", "Predictive warning scheduler is unavailable", 503)
        recipients = self.repository.list_predictive_recipients()
        counters: dict[str, int | str] = {"enqueued": 0, "reused": 0, "failed": 0}
        for recipient in recipients:
            user_id = str(recipient["user_id"])
            idempotency_key = (
                f"predictive-warning:{episode['episode_id']}:{episode['severity']}:{user_id}"
            )
            task_id = str(uuid5(NAMESPACE_URL, f"airguard:{idempotency_key}"))
            payload = {
                "episode_id": str(episode["episode_id"]),
                "recipient_user_id": user_id,
                "idempotency_key": idempotency_key,
            }
            try:
                job, created = self._reserve_job(
                    task_id,
                    "predictive_warning_notification",
                    idempotency_key,
                    payload,
                )
                if not created and job.get("status") != "FAILURE":
                    counters["reused"] = int(counters["reused"]) + 1
                    continue
                dispatch_id = str(job.get("task_id") or task_id)
                self.notification_task.apply_async(kwargs=payload, task_id=dispatch_id)
                counters["enqueued"] = int(counters["enqueued"]) + 1
                self._audit(
                    "predictive_warning.notification.enqueued",
                    episode,
                    correlation_id,
                    "success",
                    {"recipient_user_id": user_id, "severity": episode["severity"]},
                )
            except Exception as exc:
                counters["failed"] = int(counters["failed"]) + 1
                self._mark_job_failed(task_id, "predictive_warning_enqueue_failed", retrying=False)
                self._audit(
                    "predictive_warning.notification.failure",
                    episode,
                    correlation_id,
                    "failure",
                    {"recipient_user_id": user_id, "reason": exc.__class__.__name__},
                )
        return counters

    def _audit(
        self,
        action: str,
        episode: dict[str, Any],
        correlation_id: str,
        outcome: str,
        details: dict[str, Any],
    ) -> None:
        self.audit.record(
            actor_type="system",
            actor_role="worker",
            action=action,
            entity_type="predictive_warning_episode",
            entity_id=str(episode["episode_id"]),
            correlation_id=correlation_id,
            outcome=outcome,
            details=details,
        )


class PredictiveWarningService:
    def __init__(
        self,
        repository: Any,
        station_service: Any,
        audit_service: Any,
        *,
        notifier: PredictiveWarningNotificationService | None = None,
        policy_version: str = "predictive-warning-policy-v1",
        threshold_rule_version: str = "pm25-threshold-v1",
        warning_threshold: float = 50,
        critical_threshold: float = 100,
        observation_max_age_seconds: int = 300,
        min_confidence: float = 0.60,
        forecast_max_age_seconds: int = 900,
        clear_evaluations: int = 2,
        lead_minutes: int = 45,
        lead_tolerance_minutes: int = 15,
        clock: Any | None = None,
        forecast_fn: Any = trend_forecast,
    ) -> None:
        self.repository = repository
        self.station_service = station_service
        self.audit = audit_service
        self.notifier = notifier
        self.policy_version = policy_version
        self.threshold_rule_version = threshold_rule_version
        self.warning_threshold = float(warning_threshold)
        self.critical_threshold = float(critical_threshold)
        self.observation_max_age_seconds = int(observation_max_age_seconds)
        self.min_confidence = float(min_confidence)
        self.forecast_max_age_seconds = int(forecast_max_age_seconds)
        self.clear_evaluations = int(clear_evaluations)
        self.lead_minutes = int(lead_minutes)
        self.lead_tolerance_minutes = int(lead_tolerance_minutes)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._forecast = forecast_fn

    @property
    def min_lead_minutes(self) -> int:
        return self.lead_minutes - self.lead_tolerance_minutes

    @property
    def max_lead_minutes(self) -> int:
        return self.lead_minutes + self.lead_tolerance_minutes

    def evaluate(self, station_id: str, *, dry_run: bool = True, correlation_id: str) -> dict[str, Any]:
        now = self._clock().astimezone(UTC)
        active = self.repository.get_active_episode(station_id, self.threshold_rule_version)
        if self.repository.has_active_pm25_alert(station_id):
            if dry_run:
                return {
                    "outcome": "blocked",
                    "reason_code": "actual_alert_active",
                    "episode": active,
                    "dry_run": True,
                    "notification_enqueued": False,
                }
            observed = self.repository.transition_episode(str(active["episode_id"]), "observed") if active else None
            if observed:
                self._audit("predictive_warning.observed", observed, correlation_id, {"reason_code": "actual_alert_active"})
            return {"outcome": "blocked", "reason_code": "actual_alert_active", "episode": observed}
        if active and self._as_datetime(active["forecast_target_at"]) < now - timedelta(minutes=15):
            if dry_run:
                return {
                    "outcome": "would_expire",
                    "reason_code": "forecast_target_elapsed",
                    "episode": active,
                    "dry_run": True,
                    "notification_enqueued": False,
                }
            expired = self.repository.transition_episode(str(active["episode_id"]), "expired")
            self._audit("predictive_warning.expired", expired, correlation_id, {"reason_code": "forecast_target_elapsed"})
            return {"outcome": "expired", "reason_code": "forecast_target_elapsed", "episode": expired}

        candidate, blocked_reason = self._candidate(station_id, now)
        if candidate is None:
            if not active or dry_run:
                return {"outcome": "blocked", "reason_code": blocked_reason}
            cleared = self.repository.increment_clear(str(active["episode_id"]))
            if int(cleared["clear_evaluation_count"]) >= self.clear_evaluations:
                resolved = self.repository.transition_episode(str(active["episode_id"]), "resolved")
                self._audit("predictive_warning.resolved", resolved, correlation_id, {"reason_code": blocked_reason})
                return {"outcome": "resolved", "reason_code": blocked_reason, "episode": resolved}
            return {"outcome": "clearing", "reason_code": blocked_reason, "episode": cleared}

        if dry_run:
            return {
                "outcome": "candidate",
                "dry_run": True,
                "reason_code": None,
                "candidate": candidate,
                "notification_enqueued": False,
            }
        episode = self._activate_candidate(active, candidate)
        lead_minutes = (self._as_datetime(episode["forecast_target_at"]) - now).total_seconds() / 60
        notification: dict[str, Any] = {"enqueued": 0, "reused": 0, "failed": 0, "reason_code": "outside_lead_window"}
        if lead_minutes < self.min_lead_minutes:
            expired = self.repository.transition_episode(str(episode["episode_id"]), "expired")
            self._audit("predictive_warning.expired", expired, correlation_id, {"reason_code": "lead_window_missed"})
            return {"outcome": "expired", "reason_code": "lead_window_missed", "episode": expired, "notification": notification}
        if lead_minutes <= self.max_lead_minutes:
            if self.notifier is None:
                raise ServiceError("scheduler_unavailable", "Predictive warning scheduler is unavailable", 503)
            notification = self.notifier.enqueue(episode, correlation_id)
        self._audit(
            "predictive_warning.evaluated",
            episode,
            correlation_id,
            {"lead_minutes": round(lead_minutes, 2), "notification": notification},
        )
        return {"outcome": "active", "reason_code": None, "episode": episode, "notification": notification}

    def _activate_candidate(
        self,
        active: dict[str, Any] | None,
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        """Keep an episode's original target while a rolling forecast remains eligible.

        Forecasts are regenerated relative to the evaluation time. Moving an existing
        target forward on every Beat tick would prevent a two-hour warning from ever
        entering the configured delivery window. An earlier target or a warning to
        critical escalation is still persisted as new evidence.
        """
        if active is None:
            return self.repository.upsert_active_episode(candidate)

        active_severity = str(active.get("severity"))
        candidate_severity = str(candidate["severity"])
        active_target = self._as_datetime(active["forecast_target_at"])
        candidate_target = self._as_datetime(candidate["forecast_target_at"])
        is_escalation = active_severity == "warning" and candidate_severity == "critical"
        is_earlier_target = candidate_target < active_target
        if is_escalation or is_earlier_target:
            return self.repository.upsert_active_episode(candidate)
        return active

    def revalidate_for_delivery(self, episode_id: str, recipient_user_id: str) -> tuple[dict[str, Any], dict[str, str]]:
        now = self._clock().astimezone(UTC)
        episode = self.repository.get_episode(episode_id)
        if episode.get("status") != "active":
            raise ServiceError("predictive_warning_not_active", "Predictive warning is no longer active", 409)
        if self.repository.has_active_pm25_alert(str(episode["station_id"])):
            raise ServiceError("actual_alert_active", "An observed PM2.5 alert is active", 409)
        recipient = self.repository.get_predictive_recipient(recipient_user_id)
        if recipient is None:
            raise ServiceError("predictive_recipient_ineligible", "Recipient is no longer eligible", 409)
        lead = (self._as_datetime(episode["forecast_target_at"]) - now).total_seconds() / 60
        if not self.min_lead_minutes <= lead <= self.max_lead_minutes:
            raise ServiceError("lead_window_missed", "Predictive warning lead window is no longer valid", 409)
        candidate, reason = self._candidate(str(episode["station_id"]), now)
        if candidate is None:
            raise ServiceError(reason or "insufficient_forecast_quality", "Predictive warning gates no longer pass", 409)
        if candidate["severity"] not in {episode["severity"], "critical"}:
            raise ServiceError("forecast_severity_changed", "Predictive warning severity no longer matches", 409)
        return episode, recipient

    def _candidate(self, station_id: str, now: datetime) -> tuple[dict[str, Any] | None, str | None]:
        station = self.station_service.get_station(station_id)
        if (
            station.get("status") != "online"
            or station.get("freshness") != "fresh"
            or station.get("is_stale") is True
            or station.get("source") != "simulator"
            or station.get("pm25") is None
        ):
            return None, "environmental_data_unavailable"
        try:
            pm25 = self._finite(station["pm25"])
            observed_at = self._as_datetime(station["updated_at"])
            observation_age = (now - observed_at).total_seconds()
            if not 0 <= observation_age <= self.observation_max_age_seconds:
                return None, "environmental_data_unavailable"
            history = self.station_service.get_forecast_history(station_id)
            forecast = self._forecast(history, 2, metric="pm25", generated_at=now)
            generated_at = self._as_datetime(forecast["generated_at"])
            confidence = self._finite(forecast["confidence"])
        except (KeyError, TypeError, ValueError, InsufficientForecastHistory, ServiceError):
            return None, "insufficient_forecast_quality"
        age = (now - generated_at).total_seconds()
        if (
            forecast.get("freshness") != "fresh"
            or not 0 <= age <= self.forecast_max_age_seconds
            or confidence < self.min_confidence
            or not forecast.get("source")
            or not forecast.get("model_version")
        ):
            return None, "insufficient_forecast_quality"

        crossing: tuple[dict[str, Any], str, float] | None = None
        for point in sorted(forecast.get("items") or [], key=lambda value: value.get("hour_offset", 99)):
            if point.get("hour_offset") not in {1, 2}:
                continue
            try:
                lower = self._finite(point["value_min"])
                value = self._finite(point["value"])
                upper = self._finite(point["value_max"])
                point_confidence = self._finite(point.get("confidence", confidence))
                target_at = self._as_datetime(point["forecast_at"])
            except (KeyError, TypeError, ValueError):
                continue
            if point_confidence < self.min_confidence or not point.get("source"):
                continue
            if lower >= self.critical_threshold:
                crossing = (point, "critical", self.critical_threshold)
            elif lower >= self.warning_threshold:
                crossing = (point, "warning", self.warning_threshold)
            else:
                continue
            crossing = ({**point, "value": value, "value_min": lower, "value_max": upper, "forecast_at": target_at}, crossing[1], crossing[2])
            break
        if crossing is None:
            return None, "forecast_threshold_not_crossed"
        point, severity, threshold = crossing
        return {
            "station_id": station_id,
            "severity": severity,
            "threshold_value": threshold,
            "threshold_rule_version": self.threshold_rule_version,
            "policy_version": self.policy_version,
            "forecast_generated_at": generated_at,
            "forecast_target_at": point["forecast_at"],
            "predicted_value": point["value"],
            "predicted_min": point["value_min"],
            "predicted_max": point["value_max"],
            "confidence": self._finite(point.get("confidence", confidence)),
            "model_version": str(forecast["model_version"]),
            "source": str(point.get("source") or forecast["source"]),
            "evidence": {
                "current": {"station_id": station_id, "observed_at": observed_at.isoformat(), "pm25": pm25, "source": "simulator"},
                "forecast": {
                    "generated_at": generated_at.isoformat(),
                    "forecast_at": point["forecast_at"].isoformat(),
                    "value": point["value"],
                    "value_min": point["value_min"],
                    "value_max": point["value_max"],
                },
            },
        }, None

    @staticmethod
    def _finite(value: Any) -> float:
        number = float(value)
        if not math.isfinite(number) or number < 0:
            raise ValueError("finite non-negative number required")
        return number

    @staticmethod
    def _as_datetime(value: Any) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ValueError("timezone-aware timestamp required")
        return value.astimezone(UTC)

    def _audit(self, action: str, episode: dict[str, Any], correlation_id: str, details: dict[str, Any]) -> None:
        self.audit.record(
            actor_type="system",
            actor_role="backend",
            action=action,
            entity_type="predictive_warning_episode",
            entity_id=str(episode["episode_id"]),
            correlation_id=correlation_id,
            details=details,
        )
