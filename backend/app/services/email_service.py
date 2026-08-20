from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Any


class AuthEmailService:
    """Dedicated email service for account authentication, verification and password reset."""

    # In-memory test outbox for test assertions in local/testing environment
    latest_outbox: list[dict[str, Any]] = []

    def __init__(self, frontend_url: str = "http://localhost:5173") -> None:
        self.frontend_url = frontend_url.rstrip("/")

    def send_verification_email(self, email: str, raw_token: str) -> bool:
        """Send email verification link with token."""
        verification_link = f"{self.frontend_url}/verify-email?token={raw_token}"
        subject = "AirGuard AI — Xác minh địa chỉ email của bạn"
        
        text_content = (
            f"Xin chào,\n\n"
            f"Cảm ơn bạn đã đăng ký tài khoản tại AirGuard AI.\n"
            f"Vui lòng nhấp vào liên kết dưới đây để xác minh địa chỉ email (liên kết có hiệu lực trong 24 giờ):\n\n"
            f"{verification_link}\n\n"
            f"Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.\n"
            f"Trân trọng,\nĐội ngũ AirGuard AI"
        )

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #0f172a; margin-bottom: 16px;">Xác minh địa chỉ Email</h2>
            <p style="color: #334155; line-height: 1.6;">Cảm ơn bạn đã đăng ký tài khoản trên hệ thống giám sát môi trường <strong>AirGuard AI</strong>.</p>
            <p style="color: #334155; line-height: 1.6;">Vui lòng bấm nút bên dưới để xác minh email của bạn (liên kết có hiệu lực trong 24 giờ):</p>
            <div style="margin: 28px 0; text-align: center;">
                <a href="{verification_link}" style="background: #10b981; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Xác minh Email ngay</a>
            </div>
            <p style="color: #64748b; font-size: 13px;">Hoặc dán đường link sau vào trình duyệt:<br><a href="{verification_link}" style="color: #0284c7;">{verification_link}</a></p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
            <p style="color: #94a3b8; font-size: 12px;">Nếu bạn không đăng ký tài khoản AirGuard AI, bạn có thể an tâm bỏ qua email này.</p>
        </div>
        """

        return self._dispatch(recipient=email, subject=subject, text=text_content, html=html_content, token=raw_token, email_type="verification")

    def send_password_reset_email(self, email: str, raw_token: str) -> bool:
        """Send password reset link with token."""
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

        return self._dispatch(recipient=email, subject=subject, text=text_content, html=html_content, token=raw_token, email_type="password_reset")

    def send_password_changed_notification(self, email: str) -> bool:
        """Send notification that password was successfully changed."""
        subject = "AirGuard AI — Mật khẩu tài khoản đã được thay đổi"
        text_content = (
            f"Xin chào,\n\n"
            f"Mật khẩu cho tài khoản {email} vừa được thay đổi thành công.\n"
            f"Mọi phiên đăng nhập trước đó đã được hủy để bảo vệ an toàn cho tài khoản của bạn.\n"
            f"Nếu bạn không thực hiện thay đổi này, vui lòng liên hệ quản trị viên ngay lập tức.\n\n"
            f"Trân trọng,\nĐội ngũ AirGuard AI"
        )
        return self._dispatch(recipient=email, subject=subject, text=text_content, html=None, token=None, email_type="password_changed")

    def _dispatch(
        self,
        *,
        recipient: str,
        subject: str,
        text: str,
        html: str | None,
        token: str | None,
        email_type: str,
    ) -> bool:
        # Record to outbox for testing / dev preview
        self.latest_outbox.append({
            "recipient": recipient,
            "subject": subject,
            "text": text,
            "html": html,
            "token": token,
            "type": email_type,
        })
        if len(self.latest_outbox) > 100:
            self.latest_outbox.pop(0)

        provider = os.getenv("NOTIFICATION_PROVIDER", "disabled").lower()
        if provider != "smtp":
            return True

        host = os.getenv("SMTP_HOST")
        sender = os.getenv("SMTP_FROM")
        if not host or not sender or "@" not in recipient:
            return False

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient
            msg.set_content(text)
            if html:
                msg.add_alternative(html, subtype="html")

            with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=10) as client:
                if os.getenv("SMTP_STARTTLS", "true").lower() in {"1", "true", "yes"}:
                    client.starttls()
                username = os.getenv("SMTP_USERNAME")
                password = os.getenv("SMTP_PASSWORD")
                if username and password:
                    client.login(username, password)
                client.send_message(msg)
            return True
        except Exception:
            return False
