from __future__ import annotations

import json
import os

import paho.mqtt.client as mqtt
from ..celery_app import celery_app
from ..services.approval_service import ApprovalStoreUnavailableError, require_approved_device_action
from .task_support import RETRY_TASK_OPTIONS, TransientTaskError, run_idempotent
from datetime import datetime, timezone
from uuid import uuid4



@celery_app.task(name="airguard.notification.send", **RETRY_TASK_OPTIONS)
def send_notification_job(self, recipient: str, message: str, idempotency_key: str) -> dict:
    task_id = self.request.id

    def operation() -> dict:
        return {
            "task_id": task_id,
            "job_type": "notification",
            "recipient": recipient,
            "message": message,
            "delivery_status": "mock_delivered",
            "todo": "Integrate an email, SMS, or push notification provider.",
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
        try:
            approval = require_approved_device_action(approval_request_id, device_id, command)
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

<<<<<<< HEAD
        command_id = str(uuid4())
        topic = f"airguard/devices/{device_id}/command"
        payload = {
            "command_id": command_id,
            "device_id": device_id,
            "action": command,
            "approval_id": approval_request_id,
            "idempotency_key": idempotency_key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
=======
        topic = f"airguard/devices/{device_id}/command"
        payload = {
            "approval_request_id": approval_request_id,
            "device_id": device_id,
            "command": command,
>>>>>>> origin/Dungpt
        }
        client = None
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.connect(os.getenv("MQTT_HOST", "localhost"), int(os.getenv("MQTT_PORT", "1883")), 30)
            client.loop_start()
            info = client.publish(topic, json.dumps(payload), qos=1)
            info.wait_for_publish(timeout=5)
        except (OSError, RuntimeError, TimeoutError, mqtt.MQTTException) as exc:
            raise TransientTaskError(f"MQTT publish failed: {exc}") from exc
        finally:
            if client is not None:
                client.loop_stop()
                client.disconnect()

        return {
            "task_id": task_id,
            "job_type": "device_command",
            "status": "published",
            "device_id": device_id,
            "topic": topic,
            "approval_request_id": approval_request_id,
        }

    return run_idempotent(task_id=task_id, idempotency_key=idempotency_key, operation=operation)
