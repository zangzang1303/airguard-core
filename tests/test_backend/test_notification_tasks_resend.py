from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.tasks.notification_tasks import send_notification_job  # noqa: E402
from app.tasks.task_support import TransientTaskError  # noqa: E402


def test_notification_task_disabled_provider_returns_not_configured() -> None:
    with patch.dict(os.environ, {"NOTIFICATION_PROVIDER": "disabled"}, clear=False):
        res = send_notification_job.apply(
            args=["manager@vinuni.edu.vn", "Có đề xuất mới cần duyệt", "proposal-notif-1"],
        ).get()

        assert res["delivery_status"] == "not_configured"
        assert res["provider"] == "disabled"


def test_notification_task_resend_success_returns_accepted_with_message_id() -> None:
    env_vars = {
        "NOTIFICATION_PROVIDER": "resend",
        "RESEND_API_KEY": "re_test_key_123",
        "RESEND_FROM_EMAIL": "no-reply@mail.example.com",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        with patch("resend.Emails.send", return_value={"id": "msg_resend_notification_123"}):
            res = send_notification_job.apply(
                args=["manager@vinuni.edu.vn", "Có đề xuất mới cần duyệt", "proposal-notif-2"],
            ).get()

            assert res["delivery_status"] == "accepted"
            assert res["provider"] == "resend"
            assert res["provider_message_id"] == "msg_resend_notification_123"


def test_notification_task_resend_transient_error_raises_retryable_error() -> None:
    env_vars = {
        "NOTIFICATION_PROVIDER": "resend",
        "RESEND_API_KEY": "re_test_key_123",
        "RESEND_FROM_EMAIL": "no-reply@mail.example.com",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        with patch("resend.Emails.send", side_effect=TimeoutError("Connection timed out")):
            with pytest.raises(TransientTaskError) as exc_info:
                # Call underlying operation directly to test TransientTaskError without eager retry loop
                send_notification_job.run(
                    recipient="manager@vinuni.edu.vn",
                    message="Có đề xuất mới cần duyệt",
                    idempotency_key="proposal-notif-3",
                )
            assert "provider_timeout" in str(exc_info.value)


def test_notification_task_resend_permanent_error_returns_failed() -> None:
    env_vars = {
        "NOTIFICATION_PROVIDER": "resend",
        "RESEND_API_KEY": "re_test_key_123",
        "RESEND_FROM_EMAIL": "no-reply@mail.example.com",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        with patch("resend.Emails.send", side_effect=Exception("401 Unauthorized: Invalid API key")):
            res = send_notification_job.apply(
                args=["manager@vinuni.edu.vn", "Có đề xuất mới cần duyệt", "proposal-notif-4"],
            ).get()

            assert res["delivery_status"] == "failed"
            assert res["provider"] == "resend"
            assert res["reason"] == "invalid_api_key"


def test_notification_task_accepts_resident_alert_subject_and_type() -> None:
    env_vars = {
        "NOTIFICATION_PROVIDER": "resend",
        "RESEND_API_KEY": "re_test_key_123",
        "RESEND_FROM_EMAIL": "no-reply@mail.example.com",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        with patch("resend.Emails.send", return_value={"id": "msg_resident_alert_123"}) as send:
            res = send_notification_job.apply(
                kwargs={
                    "recipient": "resident@vinuni.edu.vn",
                    "message": "PM2.5 vượt ngưỡng.",
                    "idempotency_key": "resident-alert-1",
                    "subject": "AirGuard — Cảnh báo môi trường tại S03",
                    "email_type": "resident_environmental_alert",
                }
            ).get()

            assert res["delivery_status"] == "accepted"
            params = send.call_args.args[0]
            assert params["subject"] == "AirGuard — Cảnh báo môi trường tại S03"
