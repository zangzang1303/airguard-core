from __future__ import annotations

import secrets

from fastapi import Request

from .database import ServiceError

CSRF_COOKIE_NAME = "airguard_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(24)


def validate_csrf(request: Request) -> bool:
    """
    Validate CSRF token for state-mutating requests when an active session cookie is present.
    Uses Double-Submit Cookie pattern.
    """
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return True

    # If no session cookie is attached, request is not an authenticated cookie session
    session_cookie = request.cookies.get("airguard_session")
    if not session_cookie:
        return True

    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get("x-csrf-token") or request.headers.get("X-CSRF-Token")

    if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
        raise ServiceError(
            "csrf_validation_failed",
            "Yêu cầu không hợp lệ do lỗi xác thực CSRF Token. Vui lòng thử lại.",
            403,
        )
    return True
