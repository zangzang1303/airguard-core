from __future__ import annotations

from typing import Any, Callable
from fastapi import Depends, Request

from ..services.auth_service import AuthService
from ..services.database import ServiceError


# Global auth_service instance reference configured in main.py lifespan
_auth_service: AuthService | None = None


def set_auth_service(auth_service: AuthService) -> None:
    global _auth_service
    _auth_service = auth_service


def get_auth_service() -> AuthService:
    if _auth_service is None:
        raise ServiceError("service_unavailable", "Auth service is not configured.", 503)
    return _auth_service


async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """
    Authenticate request via HttpOnly session cookie 'airguard_session'.
    Strictly forbids demo headers (X-User-ID / X-User-Role).
    """
    session_cookie = request.cookies.get("airguard_session")
    if not session_cookie:
        raise ServiceError("unauthenticated", "Yêu cầu đăng nhập để truy cập.", 401)

    return auth_service.get_me(raw_session_token=session_cookie)


async def get_optional_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any] | None:
    """Optional authentication for endpoints that support both anonymous and logged-in users."""
    session_cookie = request.cookies.get("airguard_session")
    if not session_cookie:
        return None
    try:
        return auth_service.get_me(raw_session_token=session_cookie)
    except Exception:
        return None


def require_role(allowed_roles: set[str]) -> Callable:
    async def role_checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_role = current_user.get("role", "").lower()
        if user_role not in allowed_roles:
            raise ServiceError(
                "permission_denied",
                "Bạn không có quyền thực hiện thao tác này.",
                403,
            )
        return current_user

    return role_checker


# Pre-configured RBAC dependencies
require_manager = require_role({"manager", "admin"})
require_admin = require_role({"admin"})
