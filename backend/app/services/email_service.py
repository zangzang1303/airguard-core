from __future__ import annotations

import logging
import os
from typing import Any

from .resend_email_provider import EmailDeliveryResult, ResendEmailProvider

logger = logging.getLogger(__name__)


class AuthEmailService:
    """Dedicated email service for account authentication, verification and password reset via Resend."""

    # In-memory test outbox for test assertions (only populated when test outbox is enabled)
    latest_outbox: list[dict[str, Any]] = []

    def __init__(
        self,
        frontend_url: str = "http://localhost:5173",
        provider: ResendEmailProvider | None = None,
    ) -> None:
        self.frontend_url = frontend_url.rstrip("/")
        self.provider = provider or ResendEmailProvider()

    def send_verification_email(
        self,
        email: str,
        raw_token: str,
        *,
        idempotency_key: str,
    ) -> EmailDeliveryResult:
        """Send email verification 6-digit OTP code using Resend provider."""
        subject = f"AirGuard AI — Mã xác minh tài khoản của bạn: {raw_token}"

        text_content = (
            f"Xin chào,\n\n"
            f"Cảm ơn bạn đã đăng ký tài khoản tại AirGuard AI.\n"
            f"Mã xác minh gồm 6 chữ số của bạn là:\n\n"
            f"    {raw_token}\n\n"
            f"Mã có hiệu lực trong 10 phút. Vui lòng nhập mã này vào trang xác nhận để kích hoạt tài khoản.\n\n"
            f"Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.\n"
            f"Trân trọng,\nĐội ngũ AirGuard AI"
        )

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 540px; margin: 0 auto; padding: 32px 24px; border: 1px solid #e2e8f0; border-radius: 16px; background: #ffffff;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="color: #0f172a; margin: 0 0 8px; font-size: 22px; font-weight: 700;">Xác nhận địa chỉ email</h2>
                <p style="color: #64748b; font-size: 14px; margin: 0;">Hệ thống giám sát chất lượng không khí <strong>AirGuard AI</strong></p>
            </div>
            <p style="color: #334155; line-height: 1.6; font-size: 14px;">Cảm ơn bạn đã đăng ký tài khoản. Vui lòng sử dụng mã xác minh dưới đây để kích hoạt tài khoản của bạn:</p>
            <div style="margin: 28px 0; padding: 20px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; text-align: center;">
                <div style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 800; letter-spacing: 10px; color: #059669; line-height: 1;">
                    {raw_token}
                </div>
                <p style="color: #166534; font-size: 12px; font-weight: 600; margin: 8px 0 0;">Mã có hiệu lực trong 10 phút</p>
            </div>
            <p style="color: #64748b; font-size: 13px; line-height: 1.5;">Tuyệt đối không chia sẻ mã này với bất kỳ ai để đảm bảo an toàn cho tài khoản.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
            <p style="color: #94a3b8; font-size: 12px; margin: 0; text-align: center;">Nếu bạn không thực hiện đăng ký tài khoản tại AirGuard AI, bạn có thể an tâm bỏ qua email này.</p>
        </div>
        """

        return self._dispatch(
            recipient=email,
            subject=subject,
            text=text_content,
            html=html_content,
            token=raw_token,
            email_type="verification",
            idempotency_key=idempotency_key,
        )

    def send_password_reset_email(
        self,
        email: str,
        raw_token: str,
        *,
        idempotency_key: str,
    ) -> EmailDeliveryResult:
        """Send password reset link with token using Resend provider."""
        reset_link = f"{self.frontend_url}/reset-password?token={raw_token}"
        subject = "AirGuard AI — Yêu cầu đặt lại mật khẩu"

        text_content = (
            f"Xin chào,\n\n"
            f"Chúng tôi đã nhận được yêu cầu đặt lại mật khẩu cho tài khoản {email}.\n"
            f"Vui lòng nhấp vào liên kết dưới đây để đặt mật khẩu mới (liên kết có hiệu lực trong 1 giờ):\n\n"
            f"{reset_link}\n\n"
            f"Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.\n"
            f"Trân trọng,\nĐội ngũ AirGuard AI"
        )

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #0f172a; margin-bottom: 16px;">Đặt lại mật khẩu</h2>
            <p style="color: #334155; line-height: 1.6;">Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản <strong>{email}</strong>.</p>
            <p style="color: #334155; line-height: 1.6;">Vui lòng bấm nút bên dưới để tạo mật khẩu mới (liên kết có hiệu lực trong 1 giờ):</p>
            <div style="margin: 28px 0; text-align: center;">
                <a href="{reset_link}" style="background: #2563eb; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Đặt lại Mật khẩu</a>
            </div>
            <p style="color: #64748b; font-size: 13px;">Hoặc dán đường link sau vào trình duyệt:<br><a href="{reset_link}" style="color: #0284c7;">{reset_link}</a></p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
            <p style="color: #94a3b8; font-size: 12px;">Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng liên hệ quản trị viên ngay lập tức.</p>
        </div>
        """

        return self._dispatch(
            recipient=email,
            subject=subject,
            text=text_content,
            html=html_content,
            token=raw_token,
            email_type="password_reset",
            idempotency_key=idempotency_key,
        )

    def send_password_changed_notification(
        self,
        email: str,
        *,
        idempotency_key: str,
    ) -> EmailDeliveryResult:
        """Send notification that password was successfully changed using Resend provider."""
        subject = "AirGuard AI — Mật khẩu tài khoản đã được thay đổi"
        text_content = (
            f"Xin chào,\n\n"
            f"Mật khẩu cho tài khoản {email} vừa được thay đổi thành công.\n"
            f"Mọi phiên đăng nhập trước đó đã được hủy để bảo vệ an toàn cho tài khoản của bạn.\n"
            f"Nếu bạn không thực hiện thay đổi này, vui lòng liên hệ quản trị viên ngay lập tức.\n\n"
            f"Trân trọng,\nĐội ngũ AirGuard AI"
        )
        return self._dispatch(
            recipient=email,
            subject=subject,
            text=text_content,
            html=None,
            token=None,
            email_type="password_changed",
            idempotency_key=idempotency_key,
        )

    def _dispatch(
        self,
        *,
        recipient: str,
        subject: str,
        text: str,
        html: str | None,
        token: str | None,
        email_type: str,
        idempotency_key: str,
    ) -> EmailDeliveryResult:
        # Record to outbox only when test outbox is enabled (test environment)
        test_outbox_enabled = (
            os.getenv("ENABLE_TEST_OUTBOX", "false").lower() in {"1", "true", "yes"}
            or os.getenv("APP_ENV", "").lower() == "testing"
        )
        if test_outbox_enabled:
            self.latest_outbox.append({
                "recipient": recipient,
                "subject": subject,
                "text": text,
                "html": html,
                "token": token,
                "type": email_type,
                "idempotency_key": idempotency_key,
            })
            if len(self.latest_outbox) > 100:
                self.latest_outbox.pop(0)

        return self.provider.send(
            recipient=recipient,
            subject=subject,
            text=text,
            html=html,
            email_type=email_type,
            idempotency_key=idempotency_key,
        )
