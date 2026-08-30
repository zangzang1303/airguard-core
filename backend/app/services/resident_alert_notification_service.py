from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from html import escape
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .audit_service import AuditService
from .job_service import mark_job_failed, reserve_job
from .user_service import UserService

RESIDENT_ALERT_POLICY_VERSION = "resident-alert-groups-v1"
ELIGIBLE_ALERT_TYPES = frozenset(
    {
        "aqi_threshold",
        "pm25_threshold",
        "co2_threshold",
        "noise_threshold",
        "temperature_threshold",
    }
)
SUPPORTED_GROUPS = frozenset({"normal", "sensitive", "outdoor_sport"})


class ResidentAlertNotificationService:
    """Queue one personalized notification per resident and alert severity.

    Thresholds and severity remain owned by ``AlertEngine``. This service only
    chooses active resident recipients and applies deterministic wording for the
    backend-owned sensitivity group. Including severity in the idempotency key
    permits one escalation notice without resending on every sensor sample.
    """

    def __init__(
        self,
        user_service: UserService,
        audit_service: AuditService,
        *,
        notification_task: Any | None,
        enabled: bool = True,
        cooldown_seconds: int = 3600,
        clock: Callable[[], datetime] | None = None,
        reserve_job_fn: Callable[..., tuple[dict[str, Any], bool]] = reserve_job,
        mark_job_failed_fn: Callable[..., None] = mark_job_failed,
    ) -> None:
        self.user_service = user_service
        self.audit = audit_service
        self.notification_task = notification_task
        self.enabled = enabled
        self.cooldown_seconds = max(60, int(cooldown_seconds))
        self._clock = clock or (lambda: datetime.now(UTC))
        self._reserve_job = reserve_job_fn
        self._mark_job_failed = mark_job_failed_fn

    def should_notify(self, alert: dict[str, Any] | None) -> bool:
        return bool(
            self.enabled
            and alert
            and alert.get("status") == "active"
            and alert.get("alert_id")
            and alert.get("station_id")
            and alert.get("alert_type") in ELIGIBLE_ALERT_TYPES
            and alert.get("severity") in {"warning", "critical"}
        )

    def notify(self, *, alert: dict[str, Any], correlation_id: str) -> dict[str, int]:
        if not self.should_notify(alert):
            return {"enqueued": 0, "reused": 0, "failed": 0}

        alert_id = str(alert["alert_id"])
        if self.notification_task is None:
            self._audit(
                action="alert.notification.skipped",
                alert_id=alert_id,
                correlation_id=correlation_id,
                outcome="skipped",
                details={"reason": "notification_dependency_missing"},
            )
            return {"enqueued": 0, "reused": 0, "failed": 0}

        try:
            recipients = self.user_service.list_resident_alert_recipients()
        except Exception as exc:
            self._audit(
                action="alert.notification.failure",
                alert_id=alert_id,
                correlation_id=correlation_id,
                outcome="failure",
                details={
                    "reason": "recipient_lookup_failed",
                    "error_type": exc.__class__.__name__,
                    "policy_version": RESIDENT_ALERT_POLICY_VERSION,
                },
            )
            return {"enqueued": 0, "reused": 0, "failed": 1}
        if not recipients:
            self._audit(
                action="alert.notification.skipped",
                alert_id=alert_id,
                correlation_id=correlation_id,
                outcome="skipped",
                details={"reason": "resident_recipient_unavailable"},
            )
            return {"enqueued": 0, "reused": 0, "failed": 0}

        counters = {"enqueued": 0, "reused": 0, "failed": 0}
        severity = str(alert["severity"])
        cooldown_bucket = int(self._clock().timestamp() // self.cooldown_seconds)
        for recipient in recipients:
            user_id = str(recipient["user_id"])
            group = self._normalize_group(recipient.get("sensitivity_group"))
            idempotency_key = (
                f"resident-alert:{alert['station_id']}:{alert['alert_type']}:"
                f"{severity}:{user_id}:{cooldown_bucket}"
            )
            task_id = str(uuid5(NAMESPACE_URL, f"airguard:{idempotency_key}"))
            payload = {
                "recipient": recipient["email"],
                "message": self._message(alert, group),
                "html": self._html_message(alert, group),
                "idempotency_key": idempotency_key,
                "subject": self._subject(alert),
                "email_type": "resident_environmental_alert",
            }
            try:
                job, created = self._reserve_job(
                    task_id,
                    "resident_alert_notification",
                    idempotency_key,
                    payload,
                )
            except Exception as exc:
                counters["failed"] += 1
                self._audit(
                    action="alert.notification.failure",
                    alert_id=alert_id,
                    correlation_id=correlation_id,
                    outcome="failure",
                    details={
                        "recipient_user_id": user_id,
                        "sensitivity_group": group,
                        "severity": severity,
                        "reason": "job_reservation_failed",
                        "error_type": exc.__class__.__name__,
                        "policy_version": RESIDENT_ALERT_POLICY_VERSION,
                    },
                )
                continue
            if not created and job.get("status") != "FAILURE":
                counters["reused"] += 1
                continue

            dispatch_task_id = str(job.get("task_id") or task_id)
            try:
                self.notification_task.apply_async(kwargs=payload, task_id=dispatch_task_id)
                counters["enqueued"] += 1
                self._audit(
                    action="alert.notification.enqueued",
                    alert_id=alert_id,
                    correlation_id=correlation_id,
                    details={
                        "recipient_user_id": user_id,
                        "sensitivity_group": group,
                        "severity": severity,
                        "cooldown_seconds": self.cooldown_seconds,
                        "policy_version": RESIDENT_ALERT_POLICY_VERSION,
                    },
                )
            except Exception as exc:
                counters["failed"] += 1
                self._mark_job_failed(
                    dispatch_task_id,
                    "resident_alert_notification_enqueue_failed",
                    retrying=False,
                )
                self._audit(
                    action="alert.notification.failure",
                    alert_id=alert_id,
                    correlation_id=correlation_id,
                    outcome="failure",
                    details={
                        "recipient_user_id": user_id,
                        "sensitivity_group": group,
                        "severity": severity,
                        "cooldown_seconds": self.cooldown_seconds,
                        "reason": exc.__class__.__name__,
                        "policy_version": RESIDENT_ALERT_POLICY_VERSION,
                    },
                )
        return counters

    @staticmethod
    def _normalize_group(group: Any) -> str:
        return str(group) if group in SUPPORTED_GROUPS else "normal"

    @staticmethod
    def _subject(alert: dict[str, Any]) -> str:
        severity = "nghiêm trọng" if alert.get("severity") == "critical" else "cảnh báo"
        station_id = str(alert.get("station_id") or "khu vực")
        alert_reference = str(alert.get("alert_id") or "")[:8]
        reference = f" · {alert_reference}" if alert_reference else ""
        return f"AirGuard — {severity.capitalize()} môi trường tại {station_id}{reference}"

    @staticmethod
    def _message(alert: dict[str, Any], group: str) -> str:
        group_advice = {
            "normal": "Hạn chế ở ngoài trời lâu và theo dõi bản cập nhật tiếp theo của AirGuard.",
            "sensitive": (
                "Ưu tiên ở trong nhà và giảm tiếp xúc ngoài trời. "
                "Nếu cảm thấy không khỏe, hãy làm theo hướng dẫn của chuyên gia y tế."
            ),
            "outdoor_sport": (
                "Tạm hoãn hoặc giảm cường độ vận động ngoài trời; "
                "chọn thời điểm hoặc khu vực có chất lượng không khí tốt hơn."
            ),
        }[group]
        title = str(alert.get("title") or "Chỉ số môi trường vượt ngưỡng")
        observed = alert.get("observed_value")
        threshold = alert.get("threshold_value")
        metric = str(alert.get("metric") or alert.get("alert_type") or "chỉ số")
        values = ""
        if observed is not None and threshold is not None:
            values = f" {metric}: {observed} (ngưỡng cảnh báo {threshold})."
        return (
            f"{title}.{values} {group_advice} "
            "Dữ liệu do simulator tạo cho MVP, không phải quan trắc chính thức hay chẩn đoán y tế."
        )

    @classmethod
    def _html_message(cls, alert: dict[str, Any], group: str) -> str:
        """Render a self-contained HTML email while retaining `_message` as text fallback."""
        severity = "NGHIÊM TRỌNG" if alert.get("severity") == "critical" else "CẢNH BÁO"
        severity_color = "#b42318" if alert.get("severity") == "critical" else "#b54708"
        title = escape(str(alert.get("title") or "Chỉ số môi trường vượt ngưỡng"))
        station_id = escape(str(alert.get("station_id") or "khu vực"))
        metric = escape(str(alert.get("metric") or alert.get("alert_type") or "chỉ số"))
        observed = escape(str(alert.get("observed_value") or "—"))
        threshold = escape(str(alert.get("threshold_value") or "—"))
        text = escape(cls._message(alert, group))
        return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{{margin:0;background:#f5f7fa;color:#172b4d;font-family:Arial,sans-serif}}.card{{max-width:640px;margin:24px auto;background:#fff;border-radius:16px;overflow:hidden}}.header{{padding:24px 28px;background:#0f766e;color:#fff}}.content{{padding:28px}}.badge{{display:inline-block;padding:5px 9px;border-radius:999px;background:{severity_color};color:#fff;font-size:12px;font-weight:700}}.values{{margin:20px 0;padding:16px;background:#f8fafc;border-radius:10px}}.values td{{padding:6px 0}}.note{{font-size:13px;color:#52606d;line-height:1.55}}</style>
</head><body><main class="card"><header class="header"><p style="margin:0 0 8px;font-size:13px">AirGuard AI · thông báo môi trường</p><h1 style="margin:0;font-size:24px">{title}</h1></header><section class="content"><span class="badge">{severity}</span><p>Trạm: <strong>{station_id}</strong></p><table class="values" role="presentation" width="100%"><tr><td>{metric} ghi nhận</td><td align="right"><strong>{observed}</strong></td></tr><tr><td>Ngưỡng cảnh báo</td><td align="right"><strong>{threshold}</strong></td></tr></table><p style="line-height:1.6">{text}</p><p class="note">Dữ liệu do simulator tạo cho MVP; không phải quan trắc chính thức, cảnh báo khẩn của cơ quan chức năng, hay tư vấn y tế.</p></section></main></body></html>"""

    def _audit(
        self,
        *,
        action: str,
        alert_id: str,
        correlation_id: str,
        details: dict[str, Any],
        outcome: str = "success",
    ) -> None:
        self.audit.record(
            actor_type="system",
            actor_role="backend",
            action=action,
            entity_type="alert",
            entity_id=alert_id,
            correlation_id=correlation_id,
            outcome=outcome,
            details=details,
        )
