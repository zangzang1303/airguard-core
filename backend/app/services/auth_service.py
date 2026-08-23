from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .audit_service import AuditService
from .auth_crypto import (
    dummy_verify_password,
    generate_token,
    hash_password,
    hash_token,
    is_valid_email,
    normalize_email,
    verify_password,
)
from .database import Database, ServiceError, dict_cursor
from .email_service import AuthEmailService


class AuthService:
    def __init__(
        self,
        db: Database,
        audit: AuditService,
        email_service: AuthEmailService,
        *,
        session_ttl_seconds: int = 604800,
        verification_token_ttl_seconds: int = 86400,
        reset_token_ttl_seconds: int = 3600,
        rate_limit_max_attempts: int = 5,
        rate_limit_lockout_seconds: int = 900,
        demo_mode_enabled: bool = True,
        google_client_id: str | None = None,
        google_client_secret: str | None = None,
        google_redirect_uri: str | None = None,
    ) -> None:
        self.db = db
        self.audit = audit
        self.email_service = email_service
        self.session_ttl_seconds = session_ttl_seconds
        self.verification_token_ttl_seconds = verification_token_ttl_seconds
        self.reset_token_ttl_seconds = reset_token_ttl_seconds
        self.rate_limit_max_attempts = rate_limit_max_attempts
        self.rate_limit_lockout_seconds = rate_limit_lockout_seconds
        self.demo_mode_enabled = demo_mode_enabled
        self.google_client_id = google_client_id
        self.google_client_secret = google_client_secret
        self.google_redirect_uri = google_redirect_uri

    def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
        sensitivity_group: str | None = "normal",
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Register a new user with safe default resident role and issue email verification token."""
        if not is_valid_email(email):
            raise ServiceError("invalid_email", "Địa chỉ email không đúng định dạng.", 422)

        if not password or len(password) < 8:
            raise ServiceError("weak_password", "Mật khẩu phải có ít nhất 8 ký tự.", 422)

        normalized = normalize_email(email)
        cleaned_name = (full_name or "").strip() or "Cư dân AirGuard"
        valid_sensitivity = sensitivity_group if sensitivity_group in {"normal", "sensitive", "outdoor_sport"} else "normal"

        pw_hash = hash_password(password)
        user_id = str(uuid4())
        raw_token = generate_token()
        token_hash = hash_token(raw_token)

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute("SELECT user_id FROM users WHERE email_normalized = %s", (normalized,))
                if cur.fetchone():
                    raise ServiceError("email_already_registered", "Địa chỉ email này đã được đăng ký trong hệ thống.", 409)

                cur.execute(
                    """
                    INSERT INTO users (
                        user_id, email, password_hash, role, full_name,
                        sensitivity_group, email_verified_at, is_active,
                        failed_login_count, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, 'resident', %s, %s, NULL, TRUE, 0, NOW(), NOW())
                    RETURNING user_id, email, role, full_name, sensitivity_group, is_active, created_at
                    """,
                    (user_id, normalized, pw_hash, cleaned_name, valid_sensitivity),
                )
                user = dict(cur.fetchone())

                cur.execute(
                    """
                    INSERT INTO email_verification_tokens (
                        token_id, user_id, token_hash, email_normalized, created_at, expires_at
                    )
                    VALUES (%s, %s, %s, %s, NOW(), NOW() + (%s * INTERVAL '1 second'))
                    """,
                    (str(uuid4()), user_id, token_hash, normalized, self.verification_token_ttl_seconds),
                )

                self.audit.record(
                    actor_type="user",
                    actor_id=user_id,
                    actor_role="resident",
                    action="auth.register",
                    entity_type="user",
                    entity_id=user_id,
                    correlation_id=correlation_id,
                    details={"email": normalized, "role": "resident"},
                    conn=conn,
                )

        # Dispatch verification email
        self.email_service.send_verification_email(normalized, raw_token)

        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "role": user["role"],
            "full_name": user["full_name"],
            "sensitivity_group": user["sensitivity_group"],
            "email_verified": False,
            "message": "Đăng ký tài khoản thành công. Vui lòng kiểm tra hộp thư để xác minh tài khoản trước khi đăng nhập.",
        }

    def update_profile(
        self,
        *,
        user_id: str,
        full_name: str | None = None,
        sensitivity_group: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Update the current user's display name and recommendation policy group."""
        cleaned_name = full_name.strip() if full_name is not None else None
        if cleaned_name == "":
            raise ServiceError("invalid_profile", "Họ và tên không được để trống.", 422)
        if sensitivity_group is not None and sensitivity_group not in {"normal", "sensitive", "outdoor_sport"}:
            raise ServiceError("invalid_sensitivity_group", "Nhóm người dùng không hợp lệ.", 422)
        if cleaned_name is None and sensitivity_group is None:
            raise ServiceError("empty_profile_update", "Chưa có thông tin hồ sơ để cập nhật.", 422)

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET full_name = COALESCE(%s, full_name),
                        sensitivity_group = COALESCE(%s, sensitivity_group),
                        updated_at = NOW()
                    WHERE user_id = %s AND is_active = TRUE
                    RETURNING user_id, email, role, full_name, sensitivity_group, is_active
                    """,
                    (cleaned_name, sensitivity_group, user_id),
                )
                user = cur.fetchone()
                if not user:
                    raise ServiceError("user_not_found", "Không tìm thấy tài khoản đang hoạt động.", 404)
                user = dict(user)
                self.audit.record(
                    actor_type="user",
                    actor_id=user_id,
                    actor_role=user["role"],
                    action="auth.profile_updated",
                    entity_type="user",
                    entity_id=user_id,
                    correlation_id=correlation_id,
                    details={
                        "full_name_changed": cleaned_name is not None,
                        "sensitivity_group": sensitivity_group,
                    },
                    conn=conn,
                )

        return {
            "user_id": str(user["user_id"]),
            "email": user["email"],
            "role": user["role"],
            "full_name": user["full_name"],
            "sensitivity_group": user["sensitivity_group"],
            "is_active": user["is_active"],
        }

    def verify_email(self, *, raw_token: str, correlation_id: str | None = None) -> dict[str, Any]:
        """Verify an email address using single-use raw token."""
        if not raw_token or len(raw_token) < 16:
            raise ServiceError("invalid_token", "Mã xác minh không hợp lệ.", 400)

        token_hash = hash_token(raw_token)

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT token_id, user_id, email_normalized, expires_at, used_at
                    FROM email_verification_tokens
                    WHERE token_hash = %s
                    """,
                    (token_hash,),
                )
                token_record = cur.fetchone()
                if not token_record or token_record["used_at"] is not None:
                    raise ServiceError(
                        "invalid_verification_token",
                        "Mã xác minh không hợp lệ hoặc đã được sử dụng trước đó.",
                        400,
                    )

                now = datetime.now(UTC)
                if token_record["expires_at"] < now:
                    raise ServiceError(
                        "verification_token_expired",
                        "Mã xác minh đã hết hạn. Vui lòng yêu cầu gửi lại liên kết xác minh mới.",
                        400,
                    )

                user_id = token_record["user_id"]
                cur.execute(
                    """
                    UPDATE email_verification_tokens
                    SET used_at = NOW()
                    WHERE token_id = %s
                    """,
                    (token_record["token_id"],),
                )

                cur.execute(
                    """
                    UPDATE users
                    SET email_verified_at = NOW()
                    WHERE user_id = %s
                    RETURNING user_id, email, role, full_name, email_verified_at
                    """,
                    (user_id,),
                )
                user = cur.fetchone()

                self.audit.record(
                    actor_type="user",
                    actor_id=str(user_id),
                    actor_role=user["role"] if user else "resident",
                    action="auth.email_verified",
                    entity_type="user",
                    entity_id=str(user_id),
                    correlation_id=correlation_id,
                    conn=conn,
                )

        return {
            "success": True,
            "message": "Xác minh email thành công! Bạn có thể đăng nhập ngay bây giờ.",
        }

    def resend_verification(self, *, email: str, correlation_id: str | None = None) -> dict[str, Any]:
        """Resend verification email with a fresh single-use token."""
        normalized = normalize_email(email)
        generic_msg = "Nếu email tồn tại trong hệ thống và chưa được xác minh, chúng tôi đã gửi liên kết xác minh mới."

        if not is_valid_email(email):
            return {"success": True, "message": generic_msg}

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT user_id, email_verified_at, is_active
                    FROM users
                    WHERE email_normalized = %s
                    """,
                    (normalized,),
                )
                user = cur.fetchone()
                if not user or user["email_verified_at"] is not None or not user["is_active"]:
                    return {"success": True, "message": generic_msg}

                user_id = user["user_id"]
                # Invalidate existing unused tokens
                cur.execute(
                    """
                    UPDATE email_verification_tokens
                    SET used_at = NOW()
                    WHERE user_id = %s AND used_at IS NULL
                    """,
                    (user_id,),
                )

                raw_token = generate_token()
                token_hash = hash_token(raw_token)

                cur.execute(
                    """
                    INSERT INTO email_verification_tokens (
                        token_id, user_id, token_hash, email_normalized, created_at, expires_at
                    )
                    VALUES (%s, %s, %s, %s, NOW(), NOW() + (%s * INTERVAL '1 second'))
                    """,
                    (str(uuid4()), user_id, token_hash, normalized, self.verification_token_ttl_seconds),
                )

                self.audit.record(
                    actor_type="user",
                    actor_id=str(user_id),
                    action="auth.resend_verification",
                    entity_type="user",
                    entity_id=str(user_id),
                    correlation_id=correlation_id,
                    conn=conn,
                )

        self.email_service.send_verification_email(normalized, raw_token)
        return {"success": True, "message": generic_msg}

    def login(
        self,
        *,
        email: str,
        password: str,
        correlation_id: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Authenticate user credentials and create a new session."""
        normalized = normalize_email(email)

        if not email or not password:
            raise ServiceError("invalid_credentials", "Email hoặc mật khẩu không chính xác.", 401)

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, password_hash, role, full_name, sensitivity_group,
                           email_verified_at, is_active, failed_login_count, locked_until
                    FROM users
                    WHERE email_normalized = %s
                    """,
                    (normalized,),
                )
                user = cur.fetchone()

                if not user:
                    dummy_verify_password()
                    self.audit.record(
                        actor_type="anonymous",
                        action="auth.login.failed",
                        outcome="failed_user_not_found",
                        correlation_id=correlation_id,
                        details={"email": normalized, "ip": ip_address},
                        conn=conn,
                    )
                    raise ServiceError("invalid_credentials", "Email hoặc mật khẩu không chính xác.", 401)

                now = datetime.now(UTC)
                if user.get("locked_until") and user["locked_until"] > now:
                    remaining_mins = max(1, int((user["locked_until"] - now).total_seconds() // 60))
                    raise ServiceError(
                        "account_locked",
                        f"Tài khoản đang bị tạm khóa do nhập sai mật khẩu nhiều lần. Vui lòng thử lại sau {remaining_mins} phút.",
                        403,
                    )

                if not user.get("is_active"):
                    raise ServiceError("account_disabled", "Tài khoản của bạn đã bị vô hiệu hóa bởi quản trị viên.", 403)

                is_valid = verify_password(password, user["password_hash"])
                if not is_valid:
                    failed_count = (user.get("failed_login_count") or 0) + 1
                    lock_clause = ""
                    params: list[Any] = [failed_count]

                    if failed_count >= self.rate_limit_max_attempts:
                        lock_clause = ", locked_until = NOW() + (%s * INTERVAL '1 second')"
                        params.append(self.rate_limit_lockout_seconds)

                    params.append(user["user_id"])
                    cur.execute(
                        f"""
                        UPDATE users
                        SET failed_login_count = %s{lock_clause}
                        WHERE user_id = %s
                        """,
                        tuple(params),
                    )

                    self.audit.record(
                        actor_type="user",
                        actor_id=str(user["user_id"]),
                        actor_role=user["role"],
                        action="auth.login.failed",
                        entity_type="user",
                        entity_id=str(user["user_id"]),
                        outcome="failed_bad_password",
                        correlation_id=correlation_id,
                        details={"failed_attempts": failed_count, "ip": ip_address},
                        conn=conn,
                    )

                    if failed_count >= self.rate_limit_max_attempts:
                        raise ServiceError(
                            "account_locked",
                            f"Tài khoản bị tạm khóa trong {self.rate_limit_lockout_seconds // 60} phút do nhập sai mật khẩu {failed_count} lần liên tiếp.",
                            403,
                        )
                    raise ServiceError("invalid_credentials", "Email hoặc mật khẩu không chính xác.", 401)

                if user.get("email_verified_at") is None:
                    raise ServiceError(
                        "email_not_verified",
                        "Địa chỉ email chưa được xác minh. Vui lòng kiểm tra hộp thư để kích hoạt tài khoản.",
                        403,
                    )

                # Reset login failure count
                cur.execute(
                    """
                    UPDATE users
                    SET failed_login_count = 0, locked_until = NULL
                    WHERE user_id = %s
                    """,
                    (user["user_id"],),
                )

                # Generate new session
                raw_session_token = generate_token()
                session_token_hash = hash_token(raw_session_token)
                session_id = str(uuid4())

                cur.execute(
                    """
                    INSERT INTO user_sessions (
                        session_id, user_id, session_token_hash, created_at, last_seen_at, expires_at
                    )
                    VALUES (%s, %s, %s, NOW(), NOW(), NOW() + (%s * INTERVAL '1 second'))
                    """,
                    (session_id, user["user_id"], session_token_hash, self.session_ttl_seconds),
                )

                self.audit.record(
                    actor_type="user",
                    actor_id=str(user["user_id"]),
                    actor_role=user["role"],
                    action="auth.login.success",
                    entity_type="user",
                    entity_id=str(user["user_id"]),
                    correlation_id=correlation_id,
                    details={"session_id": session_id, "ip": ip_address},
                    conn=conn,
                )

                user_info = {
                    "user_id": str(user["user_id"]),
                    "email": user["email"],
                    "role": user["role"],
                    "full_name": user["full_name"],
                    "sensitivity_group": user["sensitivity_group"],
                    "is_active": user["is_active"],
                    "email_verified": True,
                }
                return raw_session_token, user_info

    def get_me(self, *, raw_session_token: str) -> dict[str, Any]:
        """Fetch current authenticated user profile from active session token."""
        if not raw_session_token:
            raise ServiceError("unauthenticated", "Yêu cầu đăng nhập để truy cập.", 401)

        token_hash = hash_token(raw_session_token)

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT s.session_id, s.expires_at, s.revoked_at,
                           u.user_id, u.email, u.role, u.full_name, u.sensitivity_group,
                           u.email_verified_at, u.is_active
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.user_id
                    WHERE s.session_token_hash = %s
                    """,
                    (token_hash,),
                )
                record = cur.fetchone()

                if not record or record["revoked_at"] is not None:
                    raise ServiceError("unauthenticated", "Phiên làm việc không tồn tại hoặc đã kết thúc.", 401)

                now = datetime.now(UTC)
                if record["expires_at"] < now:
                    raise ServiceError("session_expired", "Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại.", 401)

                if not record["is_active"]:
                    raise ServiceError("account_disabled", "Tài khoản của bạn đã bị vô hiệu hóa.", 403)

                # Touch last_seen_at
                cur.execute(
                    """
                    UPDATE user_sessions
                    SET last_seen_at = NOW()
                    WHERE session_id = %s
                    """,
                    (record["session_id"],),
                )

                return {
                    "user_id": str(record["user_id"]),
                    "email": record["email"],
                    "role": record["role"],
                    "full_name": record["full_name"],
                    "sensitivity_group": record["sensitivity_group"],
                    "email_verified": record["email_verified_at"] is not None,
                    "is_active": record["is_active"],
                }

    def logout(self, *, raw_session_token: str, correlation_id: str | None = None) -> dict[str, Any]:
        """Revoke current user session in database."""
        if not raw_session_token:
            return {"success": True, "message": "Đã đăng xuất an toàn."}

        token_hash = hash_token(raw_session_token)

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE user_sessions
                    SET revoked_at = NOW()
                    WHERE session_token_hash = %s AND revoked_at IS NULL
                    RETURNING session_id, user_id
                    """,
                    (token_hash,),
                )
                session = cur.fetchone()
                if session:
                    self.audit.record(
                        actor_type="user",
                        actor_id=str(session["user_id"]),
                        action="auth.logout",
                        entity_type="user_session",
                        entity_id=str(session["session_id"]),
                        correlation_id=correlation_id,
                        conn=conn,
                    )

        return {"success": True, "message": "Đã đăng xuất an toàn."}

    def forgot_password(self, *, email: str, correlation_id: str | None = None) -> dict[str, Any]:
        """Initiate password reset flow for email."""
        normalized = normalize_email(email)
        generic_msg = "Nếu địa chỉ email tồn tại và đã được kích hoạt, bạn sẽ nhận được email hướng dẫn đặt lại mật khẩu trong ít phút."

        if not is_valid_email(email):
            return {"success": True, "message": generic_msg}

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT user_id, email_verified_at, is_active
                    FROM users
                    WHERE email_normalized = %s
                    """,
                    (normalized,),
                )
                user = cur.fetchone()
                if not user or user["email_verified_at"] is None or not user["is_active"]:
                    return {"success": True, "message": generic_msg}

                user_id = user["user_id"]
                # Invalidate any older unused reset tokens
                cur.execute(
                    """
                    UPDATE password_reset_tokens
                    SET used_at = NOW()
                    WHERE user_id = %s AND used_at IS NULL
                    """,
                    (user_id,),
                )

                raw_token = generate_token()
                token_hash = hash_token(raw_token)

                cur.execute(
                    """
                    INSERT INTO password_reset_tokens (
                        token_id, user_id, token_hash, created_at, expires_at
                    )
                    VALUES (%s, %s, %s, NOW(), NOW() + (%s * INTERVAL '1 second'))
                    """,
                    (str(uuid4()), user_id, token_hash, self.reset_token_ttl_seconds),
                )

                self.audit.record(
                    actor_type="user",
                    actor_id=str(user_id),
                    action="auth.password_reset_requested",
                    entity_type="user",
                    entity_id=str(user_id),
                    correlation_id=correlation_id,
                    conn=conn,
                )

        self.email_service.send_password_reset_email(normalized, raw_token)
        return {"success": True, "message": generic_msg}

    def reset_password(
        self,
        *,
        raw_token: str,
        new_password: str,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Reset password using a single-use token and revoke all prior active user sessions."""
        if not raw_token or len(raw_token) < 16:
            raise ServiceError("invalid_token", "Mã đặt lại mật khẩu không hợp lệ.", 400)

        if not new_password or len(new_password) < 8:
            raise ServiceError("weak_password", "Mật khẩu mới phải có ít nhất 8 ký tự.", 422)

        token_hash = hash_token(raw_token)
        pw_hash = hash_password(new_password)

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT token_id, user_id, expires_at, used_at
                    FROM password_reset_tokens
                    WHERE token_hash = %s
                    """,
                    (token_hash,),
                )
                token_record = cur.fetchone()
                if not token_record or token_record["used_at"] is not None:
                    raise ServiceError(
                        "invalid_reset_token",
                        "Mã đặt lại mật khẩu không hợp lệ hoặc đã được sử dụng.",
                        400,
                    )

                now = datetime.now(UTC)
                if token_record["expires_at"] < now:
                    raise ServiceError(
                        "reset_token_expired",
                        "Mã đặt lại mật khẩu đã hết hạn. Vui lòng yêu cầu lại liên kết mới.",
                        400,
                    )

                user_id = token_record["user_id"]
                cur.execute("SELECT email, is_active FROM users WHERE user_id = %s", (user_id,))
                user = cur.fetchone()
                if not user or not user["is_active"]:
                    raise ServiceError("account_disabled", "Tài khoản không hợp lệ hoặc đã bị vô hiệu hóa.", 403)

                # Mark token used
                cur.execute(
                    """
                    UPDATE password_reset_tokens
                    SET used_at = NOW()
                    WHERE token_id = %s
                    """,
                    (token_record["token_id"],),
                )

                # Update password hash & reset failed login counters
                cur.execute(
                    """
                    UPDATE users
                    SET password_hash = %s,
                        password_changed_at = NOW(),
                        failed_login_count = 0,
                        locked_until = NULL
                    WHERE user_id = %s
                    """,
                    (pw_hash, user_id),
                )

                # CRITICAL: Revoke all active sessions
                cur.execute(
                    """
                    UPDATE user_sessions
                    SET revoked_at = NOW()
                    WHERE user_id = %s AND revoked_at IS NULL
                    """,
                    (user_id,),
                )

                self.audit.record(
                    actor_type="user",
                    actor_id=str(user_id),
                    action="auth.password_changed",
                    entity_type="user",
                    entity_id=str(user_id),
                    correlation_id=correlation_id,
                    conn=conn,
                )

        self.email_service.send_password_changed_notification(user["email"])
        return {
            "success": True,
            "message": "Đặt lại mật khẩu thành công! Tất cả phiên đăng nhập cũ đã được hủy. Vui lòng đăng nhập với mật khẩu mới.",
        }

    def demo_login(
        self,
        *,
        persona: str,
        correlation_id: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Quick demo login strictly restricted by allowlist and server-side AUTH_DEMO_MODE flag."""
        if not self.demo_mode_enabled:
            raise ServiceError("not_found", "Chức năng đăng nhập demo bị vô hiệu hóa trên hệ thống.", 404)

        persona_map = {
            "resident": "resident@vinuni.edu.vn",
            "sensitive": "sensitive.demo@airguard.local",
            "outdoor_sport": "outdoor.demo@airguard.local",
            "manager": "manager@vinuni.edu.vn",
            "admin": "admin@vinuni.edu.vn",
        }
        normalized_persona = (persona or "").strip().lower()
        if normalized_persona not in persona_map:
            raise ServiceError(
                "invalid_persona",
                "Persona demo không hợp lệ. Chỉ chấp nhận resident, manager hoặc admin.",
                422,
            )

        target_email = persona_map[normalized_persona]

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, password_hash, role, full_name, sensitivity_group,
                           email_verified_at, is_active, failed_login_count, locked_until
                    FROM users
                    WHERE email_normalized = %s
                    """,
                    (target_email,),
                )
                user = cur.fetchone()

                if not user:
                    # If DB was not seeded yet, create demo user record with verified email
                    user_id = str(uuid4())
                    role_map = {
                        "resident": "resident",
                        "sensitive": "resident",
                        "outdoor_sport": "resident",
                        "manager": "manager",
                        "admin": "admin",
                    }
                    name_map = {
                        "sensitive": "Cư dân Nhạy cảm Demo",
                        "outdoor_sport": "Cư dân Hoạt động ngoài trời Demo",
                        "resident": "Cư dân Demo",
                        "manager": "Quản lý Demo",
                        "admin": "Quản trị viên Demo",
                    }
                    group_map = {
                        "resident": "normal",
                        "sensitive": "sensitive",
                        "outdoor_sport": "outdoor_sport",
                        "manager": "normal",
                        "admin": "normal",
                    }
                    cur.execute(
                        """
                        INSERT INTO users (
                            user_id, email, password_hash, role, full_name,
                            sensitivity_group, email_verified_at, is_active,
                            failed_login_count, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), TRUE, 0, NOW(), NOW())
                        RETURNING user_id, email, role, full_name, sensitivity_group, email_verified_at, is_active
                        """,
                        (
                            user_id,
                            target_email,
                            hash_password("AirGuard@2026"),
                            role_map[normalized_persona],
                            name_map[normalized_persona],
                            group_map[normalized_persona],
                        ),
                    )
                    user = dict(cur.fetchone())
                else:
                    user = dict(user)

                if not user["is_active"]:
                    raise ServiceError("account_disabled", "Tài khoản demo đã bị vô hiệu hóa.", 403)

                # Reset lockout counters on successful demo login
                cur.execute(
                    """
                    UPDATE users
                    SET failed_login_count = 0, locked_until = NULL
                    WHERE user_id = %s
                    """,
                    (user["user_id"],),
                )

                # Issue valid server session
                raw_session_token = generate_token()
                session_token_hash = hash_token(raw_session_token)
                session_id = str(uuid4())

                cur.execute(
                    """
                    INSERT INTO user_sessions (
                        session_id, user_id, session_token_hash, created_at,
                        last_seen_at, expires_at, revoked_at
                    )
                    VALUES (%s, %s, %s, NOW(), NOW(), NOW() + (%s * INTERVAL '1 second'), NULL)
                    """,
                    (session_id, user["user_id"], session_token_hash, self.session_ttl_seconds),
                )

                self.audit.record(
                    actor_type="system",
                    actor_id=str(user["user_id"]),
                    actor_role=user["role"],
                    action="auth.demo_login",
                    entity_type="user",
                    entity_id=str(user["user_id"]),
                    correlation_id=correlation_id,
                    details={"persona": normalized_persona, "ip": ip_address},
                    conn=conn,
                )

        user_info = {
            "user_id": str(user["user_id"]),
            "email": user["email"],
            "role": user["role"],
            "full_name": user.get("full_name") or "Người dùng Demo",
            "sensitivity_group": user.get("sensitivity_group") or "normal",
            "email_verified": bool(user.get("email_verified_at")),
        }
        return raw_session_token, user_info

    def get_google_auth_url(self, *, state: str | None = None) -> str:
        """Construct Google OAuth 2.0 / OpenID Connect authorization URL."""
        if not self.google_client_id:
            raise ServiceError("oauth_not_configured", "Google OAuth chưa được cấu hình trên máy chủ.", 503)

        redirect_uri = self.google_redirect_uri or "http://localhost:8000/api/v1/auth/google/callback"
        oauth_state = state or generate_token()

        import urllib.parse

        params = {
            "client_id": self.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": oauth_state,
            "access_type": "offline",
            "prompt": "select_account",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

    def handle_google_callback(
        self,
        *,
        code: str,
        state: str | None = None,
        client_ip: str | None = None,
        correlation_id: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Exchange Google authorization code and create server-side session."""
        if not code or not code.strip():
            raise ServiceError("invalid_oauth_code", "Mã xác thực Google không hợp lệ hoặc đã bị hủy.", 400)

        # In testing/mock environments where GOOGLE_CLIENT_ID is unset or mocked
        email: str
        name: str
        if not self.google_client_id or not self.google_client_secret:
            # Fallback for dev / integration mock
            email = f"google.user.{code[:8]}@gmail.com"
            name = "Google User"
        else:
            import json
            import urllib.parse
            import urllib.request

            redirect_uri = self.google_redirect_uri or "http://localhost:8000/api/v1/auth/google/callback"
            token_url = "https://oauth2.googleapis.com/token"
            token_payload = urllib.parse.urlencode({
                "code": code,
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }).encode("utf-8")

            try:
                req = urllib.request.Request(
                    token_url,
                    data=token_payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    token_data = json.loads(resp.read().decode("utf-8"))
                access_token = token_data.get("access_token")

                # Fetch user info
                userinfo_req = urllib.request.Request(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                with urllib.request.urlopen(userinfo_req, timeout=10) as resp:
                    userinfo = json.loads(resp.read().decode("utf-8"))

                email = userinfo.get("email")
                name = userinfo.get("name", "Người dùng Google")
                if not email or not is_valid_email(email):
                    raise ServiceError("invalid_google_profile", "Không thể lấy email từ hồ sơ Google.", 400)
            except ServiceError:
                raise
            except Exception as exc:
                raise ServiceError("oauth_exchange_failed", "Xác thực với Google thất bại. Vui lòng thử lại.", 502) from exc

        normalized_email = normalize_email(email)

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, password_hash, role, full_name, sensitivity_group,
                           email_verified_at, is_active
                    FROM users
                    WHERE email_normalized = %s
                    """,
                    (normalized_email,),
                )
                user = cur.fetchone()

                if not user:
                    # New Google user: strictly assigned default lowest role 'resident'
                    user_id = str(uuid4())
                    cur.execute(
                        """
                        INSERT INTO users (
                            user_id, email, password_hash, role, full_name,
                            sensitivity_group, email_verified_at, is_active,
                            failed_login_count, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, 'resident', %s, 'normal', NOW(), TRUE, 0, NOW(), NOW())
                        RETURNING user_id, email, role, full_name, sensitivity_group, email_verified_at, is_active
                        """,
                        (user_id, normalized_email, hash_password(generate_token()), name),
                    )
                    user = dict(cur.fetchone())
                else:
                    user = dict(user)
                    if not user["is_active"]:
                        raise ServiceError("account_disabled", "Tài khoản của bạn đã bị vô hiệu hóa.", 403)
                    # Automatically mark email verified if coming from Google
                    if not user.get("email_verified_at"):
                        cur.execute(
                            "UPDATE users SET email_verified_at = NOW() WHERE user_id = %s",
                            (user["user_id"],),
                        )
                        user["email_verified_at"] = datetime.now(UTC)

                # Issue valid session
                raw_session_token = generate_token()
                session_token_hash = hash_token(raw_session_token)
                session_id = str(uuid4())

                cur.execute(
                    """
                    INSERT INTO user_sessions (
                        session_id, user_id, session_token_hash, created_at,
                        last_seen_at, expires_at, revoked_at
                    )
                    VALUES (%s, %s, %s, NOW(), NOW(), NOW() + (%s * INTERVAL '1 second'), NULL)
                    """,
                    (session_id, user["user_id"], session_token_hash, self.session_ttl_seconds),
                )

                self.audit.record(
                    actor_type="user",
                    actor_id=str(user["user_id"]),
                    actor_role=user["role"],
                    action="auth.google_login",
                    entity_type="user",
                    entity_id=str(user["user_id"]),
                    correlation_id=correlation_id,
                    details={"email": normalized_email, "ip": client_ip},
                    conn=conn,
                )

        user_info = {
            "user_id": str(user["user_id"]),
            "email": user["email"],
            "role": user["role"],
            "full_name": user.get("full_name") or "Người dùng Google",
            "sensitivity_group": user.get("sensitivity_group") or "normal",
            "email_verified": True,
        }
        return raw_session_token, user_info
