from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Literal

import resend

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailDeliveryResult:
    """Structured result for an email dispatch attempt via Resend Email API.

    status values:
      "accepted"        — Resend API accepted the request and returned a valid message ID.
      "not_configured"  — Provider is disabled or required credentials (API key/sender) are missing.
      "failed"          — Request was rejected by the provider or network failure occurred.
    """

    status: Literal["accepted", "not_configured", "failed"]
    provider: str
    reason_code: str | None = None
    retryable: bool = False
    provider_message_id: str | None = None


class ResendEmailProvider:
    """Shared Resend Email API adapter for Auth and Celery notification services."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None,
        timeout_seconds: int | None = None,
        provider_name: str | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("RESEND_API_KEY")
        self.from_email = from_email if from_email is not None else os.getenv("RESEND_FROM_EMAIL")
        self.from_name = from_name if from_name is not None else os.getenv("RESEND_FROM_NAME", "AirGuard AI")
        self.reply_to = reply_to if reply_to is not None else os.getenv("RESEND_REPLY_TO")
        timeout_env = os.getenv("RESEND_TIMEOUT_SECONDS", "10")
        try:
            self.timeout_seconds = timeout_seconds if timeout_seconds is not None else int(timeout_env)
        except ValueError:
            self.timeout_seconds = 10
        self.provider_name = provider_name if provider_name is not None else os.getenv("NOTIFICATION_PROVIDER", "disabled")

    def send(
        self,
        *,
        recipient: str,
        subject: str,
        text: str,
        html: str | None = None,
        email_type: str,
        idempotency_key: str,
    ) -> EmailDeliveryResult:
        """Send an email using Resend Python SDK with idempotency key.

        Never logs or exposes API keys or raw token content.
        """
        provider = (self.provider_name or "disabled").lower()
        if provider == "disabled":
            logger.info("email.dispatch.not_configured type=%s provider=disabled reason=provider_disabled", email_type)
            return EmailDeliveryResult(
                status="not_configured",
                provider="disabled",
                reason_code="provider_disabled",
            )

        if provider != "resend":
            logger.info("email.dispatch.not_configured type=%s provider=%s reason=unsupported_provider", email_type, provider)
            return EmailDeliveryResult(
                status="not_configured",
                provider=provider,
                reason_code="unsupported_provider",
            )

        if not self.api_key or not self.api_key.strip():
            logger.warning("email.dispatch.not_configured type=%s provider=resend reason=missing_api_key_config", email_type)
            return EmailDeliveryResult(
                status="not_configured",
                provider="resend",
                reason_code="missing_api_key_config",
            )

        if not self.from_email or not self.from_email.strip() or not recipient or "@" not in recipient:
            logger.warning("email.dispatch.not_configured type=%s provider=resend reason=missing_sender_config", email_type)
            return EmailDeliveryResult(
                status="not_configured",
                provider="resend",
                reason_code="missing_sender_config",
            )

        sender = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email

        params: resend.Emails.SendParams = {
            "from": sender,
            "to": [recipient],
            "subject": subject,
            "text": text,
        }
        if html:
            params["html"] = html
        if self.reply_to and self.reply_to.strip():
            params["reply_to"] = self.reply_to.strip()

        try:
            resend.api_key = self.api_key.strip()
            resend.default_http_client = resend.RequestsClient(timeout=self.timeout_seconds)

            response = resend.Emails.send(
                params,
                {"idempotency_key": idempotency_key},
            )

            message_id: str | None = None
            if isinstance(response, dict):
                message_id = response.get("id")
            elif hasattr(response, "id"):
                message_id = getattr(response, "id")

            if message_id:
                logger.info(
                    "email.dispatch.accepted type=%s provider=resend message_id=%s",
                    email_type,
                    message_id,
                )
                return EmailDeliveryResult(
                    status="accepted",
                    provider="resend",
                    provider_message_id=str(message_id),
                )

            logger.warning(
                "email.dispatch.failed type=%s provider=resend reason=invalid_provider_response",
                email_type,
            )
            return EmailDeliveryResult(
                status="failed",
                provider="resend",
                reason_code="invalid_provider_response",
                retryable=False,
            )

        except Exception as exc:
            reason_code, retryable = self._map_exception(exc)
            logger.warning(
                "email.dispatch.failed type=%s provider=resend reason=%s retryable=%s",
                email_type,
                reason_code,
                retryable,
            )
            return EmailDeliveryResult(
                status="failed",
                provider="resend",
                reason_code=reason_code,
                retryable=retryable,
            )

    @staticmethod
    def _map_exception(exc: Exception) -> tuple[str, bool]:
        """Map Resend SDK / HTTP client exceptions to safe reason codes and retryable flag.

        Does not leak exception details or secrets.
        """
        exc_str = str(exc).lower()
        exc_cls = exc.__class__.__name__.lower()

        # 1. Authentication / Invalid API Key (401)
        if "invalid_api_key" in exc_str or "api_key" in exc_cls or "401" in exc_str or "unauthorized" in exc_str:
            return "invalid_api_key", False

        # 2. Forbidden / Domain unverified (403)
        if "403" in exc_str or "forbidden" in exc_str or "domain" in exc_str or "not verified" in exc_str:
            return "sender_not_verified", False

        # 3. Validation / Bad request (400, 422)
        if "400" in exc_str or "422" in exc_str or "validation" in exc_str or "invalid" in exc_str:
            if "idempotency" in exc_str:
                return "invalid_idempotency_key", False
            return "invalid_request", False

        # 4. Conflict / Idempotency conflict (409)
        if "409" in exc_str or "conflict" in exc_str or "idempotent" in exc_str:
            if "concurrent" in exc_str:
                return "idempotency_conflict", True
            return "idempotency_conflict", False

        # 5. Rate limiting (429)
        if "429" in exc_str or "rate" in exc_str or "ratelimit" in exc_cls:
            return "rate_limited", True

        # 6. Quota exceeded
        if "quota" in exc_str:
            return "quota_exceeded", True

        # 7. Timeouts & Connection / 5xx errors (retryable)
        if "timeout" in exc_str or "timeout" in exc_cls:
            return "provider_timeout", True

        if "500" in exc_str or "502" in exc_str or "503" in exc_str or "504" in exc_str or "connection" in exc_str or "network" in exc_str:
            return "provider_unavailable", True

        # Default fallback
        return "provider_rejected", False
