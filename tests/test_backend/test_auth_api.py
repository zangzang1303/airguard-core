from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from fastapi.testclient import TestClient

from app.core import Settings
from app.dependencies.auth import set_auth_service
from app.main import app
from app.services.audit_service import AuditService
from app.services.auth_crypto import hash_password
from app.services.auth_service import AuthService
from app.services.database import Database
from app.services.email_service import AuthEmailService
from tests.test_backend.test_auth_service import FakeDatabase


def setup_test_app() -> tuple[TestClient, FakeDatabase, AuthEmailService]:
    import app.main as main_mod

    fake_db = FakeDatabase()
    email_service = AuthEmailService()
    email_service.latest_outbox.clear()
    audit_service = AuditService(fake_db)  # type: ignore[arg-type]

    auth_service = AuthService(
        fake_db,  # type: ignore[arg-type]
        audit_service,
        email_service,
        session_ttl_seconds=604800,
        verification_token_ttl_seconds=86400,
        reset_token_ttl_seconds=3600,
        rate_limit_max_attempts=5,
        rate_limit_lockout_seconds=900,
    )
    set_auth_service(auth_service)
    main_mod.db = fake_db
    main_mod.approval_service = main_mod.ApprovalService(fake_db, audit_service)

    client = TestClient(app)
    return client, fake_db, email_service


def test_csrf_endpoint_and_cookie() -> None:
    client, _, _ = setup_test_app()
    res = client.get("/api/v1/auth/csrf")

    assert res.status_code == 200
    data = res.json()
    assert "csrf_token" in data
    assert len(data["csrf_token"]) >= 20
    assert "airguard_csrf" in res.cookies


def test_e2e_register_verify_login_and_logout_flow() -> None:
    client, fake_db, email_service = setup_test_app()

    # 1. Register
    reg_payload = {
        "email": "Resident.New@VinUni.Edu.VN",
        "password": "StrongPassword2026!",
        "full_name": "Phan Thi Lan",
        "sensitivity_group": "outdoor_sport",
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 201
    assert res_reg.json()["role"] == "resident"
    assert res_reg.json()["email_verified"] is False
    assert len(email_service.latest_outbox) == 1
    raw_token = email_service.latest_outbox[0]["token"]

    # 2. Login fails before email verification
    res_login_early = client.post(
        "/api/v1/auth/login",
        json={"email": "resident.new@vinuni.edu.vn", "password": "StrongPassword2026!"},
    )
    assert res_login_early.status_code == 403
    assert res_login_early.json()["code"] == "email_not_verified"

    # 3. Verify email
    res_verify = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert res_verify.status_code == 200
    assert res_verify.json()["success"] is True

    # 4. Login succeeds and sets HttpOnly session cookie
    res_login = client.post(
        "/api/v1/auth/login",
        json={"email": "resident.new@vinuni.edu.vn", "password": "StrongPassword2026!"},
    )
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert login_data["user"]["email"] == "resident.new@vinuni.edu.vn"
    assert login_data["user"]["role"] == "resident"
    assert "airguard_session" in res_login.cookies
    assert "airguard_csrf" in res_login.cookies

    # 5. Access /api/v1/auth/me using session cookie
    client.cookies.set("airguard_session", res_login.cookies["airguard_session"])
    res_me = client.get("/api/v1/auth/me")
    assert res_me.status_code == 200
    assert res_me.json()["user"]["email"] == "resident.new@vinuni.edu.vn"

    # 6. Logout
    res_logout = client.post("/api/v1/auth/logout")
    assert res_logout.status_code == 200
    assert res_logout.json()["success"] is True


def test_rbac_protection_on_privileged_endpoints() -> None:
    client, fake_db, _ = setup_test_app()

    # Pre-seed resident and manager
    resident_id = str(uuid4())
    manager_id = str(uuid4())

    fake_db.users[resident_id] = {
        "user_id": resident_id,
        "email": "resident@vinuni.edu.vn",
        "email_normalized": "resident@vinuni.edu.vn",
        "password_hash": hash_password("ResidentPassword2026!"),
        "role": "resident",
        "full_name": "Resident A",
        "sensitivity_group": "normal",
        "email_verified_at": datetime.now(timezone.utc),
        "is_active": True,
        "failed_login_count": 0,
        "locked_until": None,
        "created_at": datetime.now(timezone.utc),
    }

    fake_db.users[manager_id] = {
        "user_id": manager_id,
        "email": "manager@vinuni.edu.vn",
        "email_normalized": "manager@vinuni.edu.vn",
        "password_hash": hash_password("ManagerPassword2026!"),
        "role": "manager",
        "full_name": "Manager B",
        "sensitivity_group": "normal",
        "email_verified_at": datetime.now(timezone.utc),
        "is_active": True,
        "failed_login_count": 0,
        "locked_until": None,
        "created_at": datetime.now(timezone.utc),
    }

    # 1. Unauthenticated request to /api/v1/approvals fails with 401
    res_unauth = client.get("/api/v1/approvals")
    assert res_unauth.status_code == 401
    assert res_unauth.json()["code"] == "unauthenticated"

    # 2. Spoofing X-User-Role / X-User-ID header without session cookie is rejected with 401
    res_spoof = client.get(
        "/api/v1/approvals",
        headers={"X-User-Role": "manager", "X-User-ID": manager_id},
    )
    assert res_spoof.status_code == 401
    assert res_spoof.json()["code"] == "unauthenticated"

    # 3. Resident login
    res_res_login = client.post(
        "/api/v1/auth/login",
        json={"email": "resident@vinuni.edu.vn", "password": "ResidentPassword2026!"},
    )
    assert res_res_login.status_code == 200
    resident_session = res_res_login.cookies["airguard_session"]

    # 4. Resident attempting to access approvals or audit logs is rejected with 403 permission_denied
    client.cookies.set("airguard_session", resident_session)
    res_perm = client.get("/api/v1/approvals")
    assert res_perm.status_code == 403
    assert res_perm.json()["code"] == "permission_denied"

    res_audit_denied = client.get("/api/v1/audit-logs")
    assert res_audit_denied.status_code == 403
    assert res_audit_denied.json()["code"] == "permission_denied"

    # 5. Resident cannot spoof role header to bypass RBAC
    res_bypass = client.get(
        "/api/v1/approvals",
        headers={"X-User-Role": "manager"},
    )
    assert res_bypass.status_code == 403
    assert res_bypass.json()["code"] == "permission_denied"

    # 6. Manager login
    res_mgr_login = client.post(
        "/api/v1/auth/login",
        json={"email": "manager@vinuni.edu.vn", "password": "ManagerPassword2026!"},
    )
    assert res_mgr_login.status_code == 200
    manager_session = res_mgr_login.cookies["airguard_session"]

    # 7. Manager access to approvals succeeds
    client.cookies.set("airguard_session", manager_session)
    res_mgr_approvals = client.get("/api/v1/approvals")
    assert res_mgr_approvals.status_code == 200
    assert "items" in res_mgr_approvals.json()


def test_auth_config_endpoint() -> None:
    client, _, _ = setup_test_app()
    res = client.get("/api/v1/auth/config")
    assert res.status_code == 200
    data = res.json()
    assert "demo_mode" in data
    assert "google_auth_enabled" in data


def test_demo_login_flow_and_rbacs() -> None:
    client, fake_db, _ = setup_test_app()

    # 1. Demo login as resident
    res_res = client.post("/api/v1/auth/demo-login", json={"persona": "resident"})
    assert res_res.status_code == 200
    data_res = res_res.json()
    assert data_res["user"]["role"] == "resident"
    assert "airguard_session" in res_res.cookies

    # 2. Demo login as manager with separate fresh client
    client.cookies.clear()
    res_mgr = client.post("/api/v1/auth/demo-login", json={"persona": "manager"})
    assert res_mgr.status_code == 200
    data_mgr = res_mgr.json()
    assert data_mgr["user"]["role"] == "manager"
    assert "airguard_session" in res_mgr.cookies

    # 3. Invalid persona is rejected
    client.cookies.clear()
    res_inv = client.post("/api/v1/auth/demo-login", json={"persona": "hacker"})
    assert res_inv.status_code == 422


def test_demo_login_disabled_returns_404() -> None:
    fake_db = FakeDatabase()
    email_service = AuthEmailService()
    audit_service = AuditService(fake_db)  # type: ignore[arg-type]

    disabled_auth_service = AuthService(
        fake_db,  # type: ignore[arg-type]
        audit_service,
        email_service,
        demo_mode_enabled=False,
    )
    set_auth_service(disabled_auth_service)

    client = TestClient(app)
    res = client.post("/api/v1/auth/demo-login", json={"persona": "resident"})
    assert res.status_code == 404
    assert res.json()["code"] == "not_found"


def test_google_oauth_callback_flow() -> None:
    client, fake_db, _ = setup_test_app()

    # Callback with valid mock code
    res = client.get("/api/v1/auth/google/callback?code=mock_google_auth_code_123&state=xyz", follow_redirects=False)
    assert res.status_code == 307
    assert "auth=google_success" in res.headers["location"]
    assert "airguard_session" in res.cookies

    # User created via Google is guaranteed resident role
    client.cookies.set("airguard_session", res.cookies["airguard_session"])
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["role"] == "resident"
    assert me.json()["user"]["email_verified"] is True

