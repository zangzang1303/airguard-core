from __future__ import annotations

import json
import os
from datetime import UTC, datetime

import paho.mqtt.client as mqtt

from ..celery_app import celery_app
from ..services.approval_service import (
    ApprovalService,
    ApprovalStoreUnavailableError,
    get_configured_default_service,
    stable_device_command_id,
)
from ..services.audit_service import AuditService
from ..services.database import Database
from ..services.job_service import mark_job_failed, reserve_job
from ..services.resend_email_provider import ResendEmailProvider
from .task_support import RETRY_TASK_OPTIONS, TransientTaskError, run_idempotent


def _wait_for_mqtt_publish(info, *, timeout_seconds: float = 5) -> None:
    info.wait_for_publish(timeout=timeout_seconds)
    if not info.is_published():
        raise TransientTaskError("MQTT QoS acknowledgement timed out")


def _close_mqtt_client(client: mqtt.Client) -> None:
    """Disconnect first so the network loop exits without waiting for its poll timeout."""
    client.disconnect()
    client.loop_stop()


def _dispatch_is_succeeded(approval: dict) -> bool:
    return (
        approval.get("command_intent_status") == "succeeded"
        or approval.get("ack_status") == "succeeded"
    )


def _task_approval_service() -> ApprovalService:
    """Use the API service in eager mode or construct the same DB-backed service in a worker."""
    configured = get_configured_default_service()
    if configured is not None:
        return configured
    database = Database(os.getenv("DATABASE_URL"))
    return ApprovalService(database, AuditService(database))


@celery_app.task(name="airguard.notification.send", **RETRY_TASK_OPTIONS)
def send_notification_job(
    self,
    recipient: str,
    message: str,
    idempotency_key: str,
    subject: str | None = None,
    email_type: str = "proposal_notification",
) -> dict:
    task_id = self.request.id

    def operation() -> dict:
        provider = ResendEmailProvider()
        resolved_subject = subject or os.getenv(
            "NOTIFICATION_SUBJECT",
            "AirGuard AI — Cảnh báo và đề xuất hành động",
        )
        result = provider.send(
            recipient=recipient,
            subject=resolved_subject,
            text=message,
            html=None,
            email_type=email_type,
            idempotency_key=idempotency_key,
        )
        if result.retryable:
            raise TransientTaskError(f"Resend delivery transient failure: {result.reason_code}")

        if result.status == "accepted":
            return {
                "task_id": task_id,
                "job_type": "notification",
                "delivery_status": "accepted",
                "provider": "resend",
                "provider_message_id": result.provider_message_id,
            }
        if result.status == "not_configured":
            return {
                "task_id": task_id,
                "job_type": "notification",
                "delivery_status": "not_configured",
                "provider": result.provider,
                "reason": result.reason_code,
            }
        return {
            "task_id": task_id,
            "job_type": "notification",
            "delivery_status": "failed",
            "provider": "resend",
            "reason": result.reason_code,
        }

    return run_idempotent(task_id=task_id, idempotency_key=idempotency_key, operation=operation)


@celery_app.task(name="airguard.device.publish_approved_command", **RETRY_TASK_OPTIONS)
def publish_approved_device_command(
    self,
    approval_request_id: str,
    device_id: str,
    command: str,
    idempotency_key: str,
) -> dict:
    task_id = self.request.id

    def operation() -> dict:
        service = _task_approval_service()
        try:
            approval = service.require_approved_device_action(approval_request_id, device_id, command)
        except ApprovalStoreUnavailableError as exc:
            raise TransientTaskError(str(exc)) from exc

        if not approval:
            return {
                "task_id": task_id,
                "job_type": "device_command",
                "status": "blocked",
                "reason": "PostgreSQL approval is missing or not approved.",
                "device_id": device_id,
            }

        command_id = approval.get("command_id") or stable_device_command_id(
            approval_request_id,
            device_id,
            command,
            idempotency_key,
        )
        control = approval.get("evidence", {}).get("control", {})
        duration_minutes = approval.get("duration_minutes", control.get("duration_minutes"))
        intensity_percent = approval.get("intensity_percent", control.get("intensity_percent"))
        if _dispatch_is_succeeded(approval):
            return {
                "task_id": task_id,
                "job_type": "device_command",
                "status": "succeeded",
                "device_id": device_id,
                "approval_request_id": approval_request_id,
                "command_id": command_id,
                "duration_minutes": duration_minutes,
                "intensity_percent": intensity_percent,
                "reused": True,
            }
        topic = f"airguard/devices/{device_id}/command"
        payload = {
            "command_id": command_id,
            "device_id": device_id,
            "action": command,
            "approval_id": approval_request_id,
            "idempotency_key": idempotency_key,
            "timestamp": datetime.now(UTC).isoformat(),
            "duration_minutes": duration_minutes,
            "intensity_percent": intensity_percent,
        }
        try:
            service.record_device_dispatch(
                request_id=approval_request_id,
                device_id=device_id,
                status="publishing",
                correlation_id=task_id,
                command_id=command_id,
            )
        except ApprovalStoreUnavailableError as exc:
            raise TransientTaskError(str(exc)) from exc
        client = None
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.connect(os.getenv("MQTT_HOST", "localhost"), int(os.getenv("MQTT_PORT", "1883")), 30)
            client.loop_start()
            info = client.publish(topic, json.dumps(payload), qos=1)
            _wait_for_mqtt_publish(info)
        except (OSError, RuntimeError, TimeoutError, mqtt.MQTTException) as exc:
            try:
                service.record_device_dispatch(
                    request_id=approval_request_id,
                    device_id=device_id,
                    status="failed",
                    correlation_id=task_id,
                    error=str(exc)[:500],
                    command_id=command_id,
                )
            except ApprovalStoreUnavailableError:
                pass
            raise TransientTaskError(f"MQTT publish failed: {exc}") from exc
        finally:
            if client is not None:
                _close_mqtt_client(client)

        service.record_device_dispatch(
            request_id=approval_request_id,
            device_id=device_id,
            status="published",
            correlation_id=task_id,
            command_id=command_id,
        )

        return {
            "task_id": task_id,
            "job_type": "device_command",
            "status": "published",
            "device_id": device_id,
            "topic": topic,
            "approval_request_id": approval_request_id,
            "command_id": command_id,
            "duration_minutes": duration_minutes,
            "intensity_percent": intensity_percent,
        }

    return run_idempotent(task_id=task_id, idempotency_key=idempotency_key, operation=operation)


@celery_app.task(name="airguard.device.reconcile_approved_commands", **RETRY_TASK_OPTIONS)
def reconcile_approved_device_commands(self, limit: int = 50) -> dict:
    """Recover approved command intents that were never durably handed to a worker."""
    service = _task_approval_service()
    try:
        candidates = service.list_dispatch_candidates(limit=limit)
    except ApprovalStoreUnavailableError as exc:
        raise TransientTaskError(str(exc)) from exc

    enqueued = 0
    skipped = 0
    failed = 0
    for candidate in candidates:
        try:
            claimed = service.claim_dispatch_candidate(str(candidate["command_intent_id"]))
        except ApprovalStoreUnavailableError as exc:
            raise TransientTaskError(str(exc)) from exc
        if not claimed:
            skipped += 1
            continue

        command_intent_id = str(claimed["command_intent_id"])
        approval_request_id = str(claimed["approval_request_id"])
        device_id = str(claimed["device_id"])
        command = str(claimed["command"])
        idempotency_key = str(claimed["idempotency_key"])
        payload = {
            "approval_request_id": approval_request_id,
            "device_id": device_id,
            "command": command,
            "idempotency_key": idempotency_key,
        }
        expected_task_id = f"device-command-{command_intent_id}"
        job, _ = reserve_job(
            expected_task_id,
            "device_command",
            idempotency_key,
            payload,
        )
        task_id = str(job.get("task_id") or expected_task_id)
        try:
            publish_approved_device_command.apply_async(kwargs=payload, task_id=task_id)
        except Exception as exc:
            mark_job_failed(task_id, "device_dispatch_enqueue_failed", retrying=False)
            try:
                service.record_device_dispatch(
                    request_id=approval_request_id,
                    device_id=device_id,
                    status="failed",
                    correlation_id=self.request.id,
                    error=str(exc)[:500],
                )
            except ApprovalStoreUnavailableError:
                pass
            failed += 1
            continue
        enqueued += 1

    return {
        "task_id": self.request.id,
        "job_type": "device_dispatch_reconciliation",
        "candidate_count": len(candidates),
        "enqueued_count": enqueued,
        "skipped_count": skipped,
        "failed_count": failed,
    }
