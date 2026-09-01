from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.services.resend_email_provider import ResendEmailProvider  # noqa: E402


def test_provider_disabled_returns_not_configured_without_sdk_call() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="sender@mail.example.com",
        provider_name="disabled",
    )
    with patch("resend.Emails.send") as mock_send:
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test body",
            email_type="verification",
            idempotency_key="auth-verification/test-1",
        )
        assert result.status == "not_configured"
        assert result.provider == "disabled"
        assert result.reason_code == "provider_disabled"
        mock_send.assert_not_called()


def test_missing_api_key_returns_not_configured() -> None:
    provider = ResendEmailProvider(
        api_key="",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send") as mock_send:
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test body",
            email_type="verification",
            idempotency_key="auth-verification/test-2",
        )
        assert result.status == "not_configured"
        assert result.provider == "resend"
        assert result.reason_code == "missing_api_key_config"
        mock_send.assert_not_called()


def test_missing_sender_or_invalid_recipient_returns_not_configured() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="",
        provider_name="resend",
    )
    with patch("resend.Emails.send") as mock_send:
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test body",
            email_type="verification",
            idempotency_key="auth-verification/test-3",
        )
        assert result.status == "not_configured"
        assert result.reason_code == "missing_sender_config"
        mock_send.assert_not_called()

    # Invalid recipient
    provider_valid_sender = ResendEmailProvider(
        api_key="re_test_123",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send") as mock_send:
        result = provider_valid_sender.send(
            recipient="invalid_email_format",
            subject="Test",
            text="Test body",
            email_type="verification",
            idempotency_key="auth-verification/test-4",
        )
        assert result.status == "not_configured"
        assert result.reason_code == "missing_sender_config"
        mock_send.assert_not_called()


def test_resend_success_returns_accepted_with_message_id() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="no-reply@mail.example.com",
        from_name="AirGuard AI",
        provider_name="resend",
        reply_to="",
    )
    with patch("resend.Emails.send", return_value={"id": "msg_abc123"}) as mock_send:
        result = provider.send(
            recipient="delivered+airguard@resend.dev",
            subject="Xác minh email",
            text="Nội dung",
            html="<p>Nội dung</p>",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-1",
        )
        assert result.status == "accepted"
        assert result.provider == "resend"
        assert result.provider_message_id == "msg_abc123"
        assert result.retryable is False

        mock_send.assert_called_once_with(
            {
                "from": "AirGuard AI <no-reply@mail.example.com>",
                "to": ["delivered+airguard@resend.dev"],
                "subject": "Xác minh email",
                "text": "Nội dung",
                "html": "<p>Nội dung</p>",
            },
            {"idempotency_key": "auth-verification/token-uuid-1"},
        )


def test_resend_missing_id_in_response_returns_failed() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send", return_value={}):
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-2",
        )
        assert result.status == "failed"
        assert result.reason_code == "invalid_provider_response"
        assert result.retryable is False


def test_invalid_api_key_returns_failed_non_retryable() -> None:
    provider = ResendEmailProvider(
        api_key="re_invalid",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send", side_effect=Exception("401 Unauthorized: Invalid API key")):
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-3",
        )
        assert result.status == "failed"
        assert result.reason_code == "invalid_api_key"
        assert result.retryable is False


def test_unverified_sender_domain_returns_failed_non_retryable() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="unverified@unverified-domain.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send", side_effect=Exception("403 Forbidden: domain not verified")):
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-4",
        )
        assert result.status == "failed"
        assert result.reason_code == "sender_not_verified"
        assert result.retryable is False


def test_validation_error_returns_failed_non_retryable() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send", side_effect=Exception("422 Unprocessable Entity: validation error")):
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-5",
        )
        assert result.status == "failed"
        assert result.reason_code == "invalid_request"
        assert result.retryable is False


def test_idempotency_conflict_non_concurrent_returns_non_retryable() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send", side_effect=Exception("409 Conflict: idempotency key conflict")):
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-6",
        )
        assert result.status == "failed"
        assert result.reason_code == "idempotency_conflict"
        assert result.retryable is False


def test_concurrent_idempotent_requests_returns_retryable() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send", side_effect=Exception("409 Conflict: concurrent_idempotent_requests")):
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-7",
        )
        assert result.status == "failed"
        assert result.reason_code == "idempotency_conflict"
        assert result.retryable is True


def test_rate_limit_and_quota_return_retryable() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send", side_effect=Exception("429 Too Many Requests: rate limited")):
        result = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-8",
        )
        assert result.status == "failed"
        assert result.reason_code == "rate_limited"
        assert result.retryable is True

    with patch("resend.Emails.send", side_effect=Exception("quota exceeded")):
        result_quota = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-9",
        )
        assert result_quota.status == "failed"
        assert result_quota.reason_code == "quota_exceeded"
        assert result_quota.retryable is True


def test_timeout_and_5xx_return_retryable() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send", side_effect=TimeoutError("Request timed out")):
        result_timeout = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-10",
        )
        assert result_timeout.status == "failed"
        assert result_timeout.reason_code == "provider_timeout"
        assert result_timeout.retryable is True

    with patch("resend.Emails.send", side_effect=Exception("503 Service Unavailable")):
        result_503 = provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Test",
            email_type="verification",
            idempotency_key="auth-verification/token-uuid-11",
        )
        assert result_503.status == "failed"
        assert result_503.reason_code == "provider_unavailable"
        assert result_503.retryable is True


def test_idempotency_key_is_always_passed_and_length_bounded() -> None:
    provider = ResendEmailProvider(
        api_key="re_test_123",
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    key = "auth-verification/" + "a" * 200
    assert len(key) <= 256
    with patch("resend.Emails.send", return_value={"id": "msg_123"}) as mock_send:
        provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Body",
            email_type="verification",
            idempotency_key=key,
        )
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][1]["idempotency_key"] == key


def test_logger_does_not_leak_secrets_or_raw_token(caplog: pytest.LogCaptureFixture) -> None:
    secret_key = "re_super_secret_api_key_99999"
    provider = ResendEmailProvider(
        api_key=secret_key,
        from_email="sender@mail.example.com",
        provider_name="resend",
    )
    with patch("resend.Emails.send", return_value={"id": "msg_safe_id"}):
        provider.send(
            recipient="user@example.com",
            subject="Test",
            text="Secret content: raw_token_secret_12345",
            email_type="verification",
            idempotency_key="auth-verification/safe-token-id",
        )
        for record in caplog.records:
            assert secret_key not in record.getMessage()
            assert "raw_token_secret_12345" not in record.getMessage()
