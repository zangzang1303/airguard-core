from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

import app.main as main_mod  # noqa: E402
from app.dependencies.auth import require_admin  # noqa: E402

ADMIN_ID = "00000000-0000-0000-0000-000000000003"
TARGET_ID = "00000000-0000-0000-0000-000000000101"


def test_admin_user_patch_requires_csrf(monkeypatch) -> None:
    async def admin_override() -> dict[str, str]:
        return {"user_id": ADMIN_ID, "role": "admin"}

    class MustNotUpdate:
        def update_user(self, **_kwargs):
            raise AssertionError("mutation must not run after CSRF rejection")

    monkeypatch.setattr(main_mod, "user_admin_service", MustNotUpdate())
    main_mod.app.dependency_overrides[require_admin] = admin_override
    try:
        client = TestClient(main_mod.app)
        client.cookies.set("airguard_session", "test-session")
        client.cookies.set("airguard_csrf", "expected")
        response = client.patch(
            f"/api/v1/users/{TARGET_ID}",
            json={"role": "manager", "reason": "Thay đổi phạm vi vận hành"},
            headers={"X-CSRF-Token": "wrong"},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "csrf_validation_failed"
    finally:
        main_mod.app.dependency_overrides.clear()


def test_admin_user_patch_returns_persisted_backend_result(monkeypatch) -> None:
    async def admin_override() -> dict[str, str]:
        return {"user_id": ADMIN_ID, "role": "admin"}

    class FakeUserAdminService:
        def update_user(self, **kwargs):
            assert kwargs["target_user_id"] == TARGET_ID
            assert kwargs["role"] == "manager"
            assert kwargs["reason"] == "Thay đổi phạm vi vận hành"
            return {
                "user": {
                    "user_id": TARGET_ID,
                    "email": "resident@vinuni.edu.vn",
                    "full_name": "Trần Minh Anh",
                    "role": "manager",
                    "user_group": "normal",
                    "status": "active",
                    "created_at": "2026-08-01T00:00:00+00:00",
                    "last_active_at": None,
                },
                "audit": {
                    "audit_id": 42,
                    "created_at": "2026-08-23T00:00:00+00:00",
                    "actor_id": ADMIN_ID,
                    "actor_role": "admin",
                    "action": "user.admin_updated",
                    "entity_type": "user",
                    "entity_id": TARGET_ID,
                    "outcome": "success",
                    "correlation_id": kwargs["correlation_id"],
                    "details": {"reason": kwargs["reason"]},
                },
            }

    monkeypatch.setattr(main_mod, "user_admin_service", FakeUserAdminService())
    main_mod.app.dependency_overrides[require_admin] = admin_override
    try:
        client = TestClient(main_mod.app)
        client.cookies.set("airguard_session", "test-session")
        client.cookies.set("airguard_csrf", "csrf-token")
        response = client.patch(
            f"/api/v1/users/{TARGET_ID}",
            json={"role": "manager", "reason": "Thay đổi phạm vi vận hành"},
            headers={"X-CSRF-Token": "csrf-token", "X-Request-ID": "admin-user-001"},
        )
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "manager"
        assert response.json()["audit"]["correlation_id"] == "admin-user-001"
    finally:
        main_mod.app.dependency_overrides.clear()
