from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

os.environ["ENABLE_TEST_OUTBOX"] = "true"
os.environ["APP_ENV"] = "test"

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.services.audit_service import AuditService  # noqa: E402
from app.services.auth_crypto import hash_password  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402
from app.services.database import ServiceError  # noqa: E402
from app.services.email_service import AuthEmailService  # noqa: E402
from app.services.resend_email_provider import ResendEmailProvider  # noqa: E402


class FakeCursor:
    def __init__(self, db: FakeDatabase) -> None:
        self.db = db
        self._last_result: list[dict[str, Any]] = []

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def execute(self, query: str, params: tuple | list = ()) -> None:
        q = " ".join(query.strip().split())
        self._last_result = []

        if "SELECT user_id FROM users WHERE email_normalized = %s" in q:
            email = params[0]
            for u in self.db.users.values():
                if u["email_normalized"] == email:
                    self._last_result.append({"user_id": u["user_id"]})

        elif "INSERT INTO users" in q and "RETURNING" in q:
            if len(params) == 6:
                user_id, email_norm, pw_hash, role, full_name, sens = params
            elif len(params) == 5:
                user_id, email_norm, pw_hash, p4, p5 = params
                if "'resident'" not in q and ("role" in q or "manager" in str(p4) or "admin" in str(p4)):
                    role = p4
                    full_name = p5
                    sens = "normal"
                else:
                    role = "resident"
                    full_name = p4
                    sens = p5
            elif len(params) == 4:
                user_id, email_norm, pw_hash, full_name = params
                role = "resident"
                sens = "normal"
            else:
                user_id, email_norm, pw_hash = params[:3]
                role = "resident"
                full_name = "User"
                sens = "normal"

            user_record = {
                "user_id": user_id,
                "email": email_norm,
                "email_normalized": email_norm,
                "password_hash": pw_hash,
                "role": role,
                "full_name": full_name,
                "sensitivity_group": sens,
                "email_verified_at": datetime.now(UTC) if "NOW(), TRUE" in q else None,
                "is_active": True,
                "failed_login_count": 0,
                "locked_until": None,
                "created_at": datetime.now(UTC),
            }
            self.db.users[user_id] = user_record
            self._last_result.append(user_record)

        elif "INSERT INTO email_verification_tokens" in q:
            token_id, user_id, token_hash_val, email_norm, ttl = params
            self.db.verification_tokens[token_hash_val] = {
                "token_id": token_id,
                "user_id": user_id,
                "token_hash": token_hash_val,
                "email_normalized": email_norm,
                "expires_at": datetime.now(UTC) + timedelta(seconds=ttl),
                "used_at": None,
            }

        elif "SELECT token_id, user_id, email_normalized, expires_at, used_at FROM email_verification_tokens WHERE token_hash = %s" in q:
            th = params[0]
            if th in self.db.verification_tokens:
                self._last_result.append(self.db.verification_tokens[th])

        elif "UPDATE email_verification_tokens SET used_at = NOW() WHERE token_id = %s" in q:
            tid = params[0]
            for t in self.db.verification_tokens.values():
                if t["token_id"] == tid:
                    t["used_at"] = datetime.now(UTC)

        elif "UPDATE email_verification_tokens SET used_at = NOW() WHERE user_id = %s AND used_at IS NULL" in q:
            uid = params[0]
            for t in self.db.verification_tokens.values():
                if t["user_id"] == uid and t["used_at"] is None:
                    t["used_at"] = datetime.now(UTC)

        elif "UPDATE users SET email_verified_at = NOW()" in q:
            uid = params[0]
            if uid in self.db.users:
                self.db.users[uid]["email_verified_at"] = datetime.now(UTC)
                self._last_result.append(self.db.users[uid])

        elif "SELECT user_id, email_verified_at, is_active FROM users WHERE email_normalized = %s" in q:
            email = params[0]
            for u in self.db.users.values():
                if u["email_normalized"] == email:
                    self._last_result.append({
                        "user_id": u["user_id"],
                        "email_verified_at": u["email_verified_at"],
                        "is_active": u["is_active"],
                    })

        elif "SELECT user_id, email, password_hash, role, full_name, sensitivity_group, email_verified_at, is_active, failed_login_count, locked_until FROM users WHERE email_normalized = %s" in q:
            email = params[0]
            for u in self.db.users.values():
                if u["email_normalized"] == email:
                    self._last_result.append(u)

        elif "UPDATE users SET full_name = COALESCE(%s, full_name), sensitivity_group = COALESCE(%s, sensitivity_group)" in q:
            full_name, sensitivity_group, uid = params
            user = self.db.users.get(uid)
            if user and user["is_active"]:
                if full_name is not None:
                    user["full_name"] = full_name
                if sensitivity_group is not None:
                    user["sensitivity_group"] = sensitivity_group
                self._last_result.append(user)

        elif "UPDATE users SET failed_login_count = 0, locked_until = NULL" in q:
            uid = params[0]
            if uid in self.db.users:
                self.db.users[uid]["failed_login_count"] = 0
                self.db.users[uid]["locked_until"] = None

        elif "UPDATE users SET failed_login_count =" in q:
            if "locked_until" in q:
                count, lockout_sec, uid = params
                self.db.users[uid]["failed_login_count"] = count
                self.db.users[uid]["locked_until"] = datetime.now(UTC) + timedelta(seconds=lockout_sec)
            else:
                count, uid = params
                self.db.users[uid]["failed_login_count"] = count

        elif "INSERT INTO user_sessions" in q:
            session_id, user_id, s_hash, ttl = params
            self.db.sessions[s_hash] = {
                "session_id": session_id,
                "user_id": user_id,
                "session_token_hash": s_hash,
                "created_at": datetime.now(UTC),
                "last_seen_at": datetime.now(UTC),
                "expires_at": datetime.now(UTC) + timedelta(seconds=ttl),
                "revoked_at": None,
            }

        elif "FROM user_sessions s JOIN users u ON s.user_id = u.user_id WHERE s.session_token_hash = %s" in q:
            s_hash = params[0]
            if s_hash in self.db.sessions:
                s = self.db.sessions[s_hash]
                u = self.db.users.get(s["user_id"])
                if u:
                    self._last_result.append({
                        "session_id": s["session_id"],
                        "expires_at": s["expires_at"],
                        "revoked_at": s["revoked_at"],
                        "user_id": u["user_id"],
                        "email": u["email"],
                        "role": u["role"],
                        "full_name": u["full_name"],
                        "sensitivity_group": u["sensitivity_group"],
                        "email_verified_at": u["email_verified_at"],
                        "is_active": u["is_active"],
                    })

        elif "UPDATE user_sessions SET last_seen_at = NOW() WHERE session_id = %s" in q:
            sid = params[0]
            for s in self.db.sessions.values():
                if s["session_id"] == sid:
                    s["last_seen_at"] = datetime.now(UTC)

        elif "UPDATE user_sessions SET revoked_at = NOW() WHERE session_token_hash = %s AND revoked_at IS NULL" in q:
            s_hash = params[0]
            if s_hash in self.db.sessions and self.db.sessions[s_hash]["revoked_at"] is None:
                self.db.sessions[s_hash]["revoked_at"] = datetime.now(UTC)
                self._last_result.append({
                    "session_id": self.db.sessions[s_hash]["session_id"],
                    "user_id": self.db.sessions[s_hash]["user_id"],
                })

        elif "UPDATE user_sessions SET revoked_at = NOW() WHERE user_id = %s AND revoked_at IS NULL" in q:
            uid = params[0]
            for s in self.db.sessions.values():
                if s["user_id"] == uid and s["revoked_at"] is None:
                    s["revoked_at"] = datetime.now(UTC)

        elif "INSERT INTO password_reset_tokens" in q:
            token_id, user_id, token_hash_val, ttl = params
            self.db.reset_tokens[token_hash_val] = {
                "token_id": token_id,
                "user_id": user_id,
                "token_hash": token_hash_val,
                "expires_at": datetime.now(UTC) + timedelta(seconds=ttl),
                "used_at": None,
            }

        elif "SELECT token_id, user_id, expires_at, used_at FROM password_reset_tokens WHERE token_hash = %s" in q:
            th = params[0]
            if th in self.db.reset_tokens:
                self._last_result.append(self.db.reset_tokens[th])

        elif "UPDATE password_reset_tokens SET used_at = NOW() WHERE token_id = %s" in q:
            tid = params[0]
            for t in self.db.reset_tokens.values():
                if t["token_id"] == tid:
                    t["used_at"] = datetime.now(UTC)

        elif "UPDATE password_reset_tokens SET used_at = NOW() WHERE user_id = %s AND used_at IS NULL" in q:
            uid = params[0]
            for t in self.db.reset_tokens.values():
                if t["user_id"] == uid and t["used_at"] is None:
                    t["used_at"] = datetime.now(UTC)

        elif "SELECT email, is_active FROM users WHERE user_id = %s" in q:
            uid = params[0]
            if uid in self.db.users:
                self._last_result.append({
                    "email": self.db.users[uid]["email"],
                    "is_active": self.db.users[uid]["is_active"],
                })

        elif "UPDATE users SET password_hash = %s, password_changed_at = NOW(), failed_login_count = 0, locked_until = NULL WHERE user_id = %s" in q:
            pw, uid = params
            if uid in self.db.users:
                self.db.users[uid]["password_hash"] = pw
                self.db.users[uid]["failed_login_count"] = 0
                self.db.users[uid]["locked_until"] = None

        elif "INSERT INTO audit_logs" in q:
            self._last_result.append({
                "audit_id": 1,
                "created_at": datetime.now(UTC),
            })

    def fetchone(self) -> dict[str, Any] | None:
        return self._last_result[0] if self._last_result else None

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self._last_result)


class FakeConnection:
    def __init__(self, db: FakeDatabase) -> None:
        self.db = db

    def __enter__(self) -> FakeConnection:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def cursor(self, *args, **kwargs) -> FakeCursor:
        return FakeCursor(self.db)


class FakeDatabase:
    def __init__(self) -> None:
        self.users: dict[str, dict[str, Any]] = {}
        self.sessions: dict[str, dict[str, Any]] = {}
        self.verification_tokens: dict[str, dict[str, Any]] = {}
        self.reset_tokens: dict[str, dict[str, Any]] = {}

    def connection(self) -> FakeConnection:
        return FakeConnection(self)

    def ping(self) -> None:
        pass


def create_test_auth_service() -> tuple[AuthService, FakeDatabase, AuthEmailService]:
    db = FakeDatabase()
    email_service = AuthEmailService()
    email_service.latest_outbox.clear()
    audit = AuditService(db)  # type: ignore[arg-type]
    service = AuthService(
        db,  # type: ignore[arg-type]
        audit,
        email_service,
        session_ttl_seconds=604800,
        verification_token_ttl_seconds=600,
        reset_token_ttl_seconds=3600,
        rate_limit_max_attempts=5,
        rate_limit_lockout_seconds=900,
    )
    return service, db, email_service


def test_register_flow_and_verification() -> None:
    service, db, email_svc = create_test_auth_service()

    # 1. Register new resident
    reg = service.register(
        email="Resident.Test@VinUni.Edu.VN",
        password="SecurePassword2026!",
        full_name="Nguyễn Văn Test",
        sensitivity_group="sensitive",
    )

    assert reg["role"] == "resident"
    assert reg["email"] == "resident.test@vinuni.edu.vn"
    assert reg["email_verified"] is False
    assert len(email_svc.latest_outbox) == 1
    raw_token = email_svc.latest_outbox[0]["token"]
    assert raw_token is not None

    # 2. Cannot login before email verification
    try:
        service.login(email="resident.test@vinuni.edu.vn", password="SecurePassword2026!")
        raise AssertionError("Login should fail for unverified email")
    except ServiceError as exc:
        assert exc.code == "email_not_verified"
        assert exc.status_code == 403

    # 3. Verify email with raw token
    verify_res = service.verify_email(raw_token=raw_token)
    assert verify_res["success"] is True

    # 4. Reusing verification token fails
    try:
        service.verify_email(raw_token=raw_token)
        raise AssertionError("Reusing verification token should fail")
    except ServiceError as exc:
        assert exc.code == "invalid_verification_token"

    # 5. Login now succeeds
    raw_session, user = service.login(email="resident.test@vinuni.edu.vn", password="SecurePassword2026!")
    assert user["email"] == "resident.test@vinuni.edu.vn"
    assert user["role"] == "resident"
    assert user["email_verified"] is True

    # 6. Session lookup via get_me
    me = service.get_me(raw_session_token=raw_session)
    assert me["email"] == "resident.test@vinuni.edu.vn"
    assert me["role"] == "resident"

    # 7. Logout revokes session
    service.logout(raw_session_token=raw_session)
    try:
        service.get_me(raw_session_token=raw_session)
        raise AssertionError("Revoked session should be rejected")
    except ServiceError as exc:
        assert exc.code == "unauthenticated"


def test_resend_email_failure_does_not_rollback_user() -> None:
    """When Resend email dispatch fails, user and token creation must not be rolled back."""
    mock_provider = ResendEmailProvider(
        provider_name="resend",
        api_key="re_test",
        from_email="no-reply@mail.example.com",
    )
    db = FakeDatabase()
    email_service = AuthEmailService(provider=mock_provider)
    audit = AuditService(db)  # type: ignore[arg-type]
    service = AuthService(db, audit, email_service)  # type: ignore[arg-type]

    with patch("resend.Emails.send", side_effect=Exception("500 Internal Server Error")):
        reg = service.register(
            email="resilience.test@vinuni.edu.vn",
            password="SecurePassword2026!",
            full_name="Nguyễn Văn Bền Vững",
        )

        assert reg["user_id"] in db.users
        assert reg["email_delivery_status"] == "failed"
        assert len(db.verification_tokens) == 1

        # Token is still valid for manual / subsequent verification
        token_hash = list(db.verification_tokens.keys())[0]
        assert db.verification_tokens[token_hash]["used_at"] is None



def test_login_rate_limiting_and_account_lockout() -> None:
    service, db, email_svc = create_test_auth_service()

    # Pre-seed verified user
    user_id = str(uuid4())
    db.users[user_id] = {
        "user_id": user_id,
        "email": "manager@vinuni.edu.vn",
        "email_normalized": "manager@vinuni.edu.vn",
        "password_hash": hash_password("ValidPassword2026!"),
        "role": "manager",
        "full_name": "Quản lý Demo",
        "sensitivity_group": "normal",
        "email_verified_at": datetime.now(UTC),
        "is_active": True,
        "failed_login_count": 0,
        "locked_until": None,
        "created_at": datetime.now(UTC),
    }

    # 4 failed attempts
    for attempt in range(1, 5):
        try:
            service.login(email="manager@vinuni.edu.vn", password="WrongPassword")
        except ServiceError as exc:
            assert exc.code == "invalid_credentials"
            assert exc.status_code == 401

    assert db.users[user_id]["failed_login_count"] == 4

    # 5th attempt locks account
    try:
        service.login(email="manager@vinuni.edu.vn", password="WrongPassword")
        raise AssertionError("5th failed attempt should lock account")
    except ServiceError as exc:
        assert exc.code == "account_locked"
        assert exc.status_code == 403

    assert db.users[user_id]["locked_until"] is not None


def test_forgot_and_reset_password_revokes_all_prior_sessions() -> None:
    service, db, email_svc = create_test_auth_service()

    # Pre-seed verified user
    user_id = str(uuid4())
    db.users[user_id] = {
        "user_id": user_id,
        "email": "user@vinuni.edu.vn",
        "email_normalized": "user@vinuni.edu.vn",
        "password_hash": hash_password("OldPassword2026!"),
        "role": "resident",
        "full_name": "Cư Dân",
        "sensitivity_group": "normal",
        "email_verified_at": datetime.now(UTC),
        "is_active": True,
        "failed_login_count": 0,
        "locked_until": None,
        "created_at": datetime.now(UTC),
    }

    # Create an active session
    session1, _ = service.login(email="user@vinuni.edu.vn", password="OldPassword2026!")
    session2, _ = service.login(email="user@vinuni.edu.vn", password="OldPassword2026!")

    assert service.get_me(raw_session_token=session1)["email"] == "user@vinuni.edu.vn"
    assert service.get_me(raw_session_token=session2)["email"] == "user@vinuni.edu.vn"

    # Request password reset
    email_svc.latest_outbox.clear()
    service.forgot_password(email="user@vinuni.edu.vn")
    assert len(email_svc.latest_outbox) == 1
    reset_raw_token = email_svc.latest_outbox[0]["token"]
    assert reset_raw_token is not None

    # Reset password with new password
    reset_res = service.reset_password(raw_token=reset_raw_token, new_password="BrandNewPassword2026!")
    assert reset_res["success"] is True

    # CRITICAL: Prior active sessions MUST be revoked immediately
    try:
        service.get_me(raw_session_token=session1)
        raise AssertionError("Session 1 should be revoked after password reset")
    except ServiceError as exc:
        assert exc.code == "unauthenticated"

    try:
        service.get_me(raw_session_token=session2)
        raise AssertionError("Session 2 should be revoked after password reset")
    except ServiceError as exc:
        assert exc.code == "unauthenticated"

    # Login with new password succeeds
    new_session, _ = service.login(email="user@vinuni.edu.vn", password="BrandNewPassword2026!")
    assert service.get_me(raw_session_token=new_session)["email"] == "user@vinuni.edu.vn"
