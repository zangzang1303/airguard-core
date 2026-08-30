from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.dependencies.auth import require_manager  # noqa: E402
from app.services.audit_service import (  # noqa: E402
    MANAGER_ACTIVITY_LOG_ACTIONS,
    AuditService,
)


def test_activity_log_is_shared_and_manager_only(monkeypatch) -> None:
    os.environ.pop("DATABASE_URL", None)
    import app.main as main_module

    decision_rows = [
        {
            "audit_id": 17,
            "actor_type": "user",
            "actor_id": "00000000-0000-0000-0000-000000000102",
            "actor_role": "manager",
            "action": "approval.approve",
            "entity_type": "approval_request",
            "entity_id": "90000000-0000-0000-0000-000000000801",
            "outcome": "success",
            "station_id": "S03",
            "created_at": "2026-08-30T08:40:00+07:00",
        },
        {
            "audit_id": 16,
            "actor_type": "user",
            "actor_id": "00000000-0000-0000-0000-000000000102",
            "actor_role": "manager",
            "action": "approval.reject",
            "entity_type": "approval_request",
            "entity_id": "90000000-0000-0000-0000-000000000802",
            "outcome": "success",
            "station_id": "S02",
            "created_at": "2026-08-30T09:10:00+07:00",
        },
    ]

    class FakeAuditService:
        def __init__(self) -> None:
            self.limits: list[int] = []

        def list_manager_activity_logs(self, *, limit: int) -> list[dict]:
            self.limits.append(limit)
            return decision_rows

    audit = FakeAuditService()
    monkeypatch.setattr(main_module, "audit_service", audit)
    client = TestClient(main_module.app)

    assert client.get("/api/v1/activity-log").status_code == 401

    try:
        main_module.app.dependency_overrides[require_manager] = lambda: {
            "user_id": "00000000-0000-0000-0000-000000000102",
            "role": "manager",
        }
        first_manager = client.get("/api/v1/activity-log?limit=25")

        main_module.app.dependency_overrides[require_manager] = lambda: {
            "user_id": "00000000-0000-0000-0000-000000000103",
            "role": "admin",
        }
        second_manager = client.get("/api/v1/activity-log?limit=25")
    finally:
        main_module.app.dependency_overrides.clear()

    assert first_manager.status_code == 200
    assert second_manager.status_code == 200
    assert first_manager.json() == second_manager.json()
    assert first_manager.json()["scope"] == "manager_decisions"
    assert {row["action"] for row in first_manager.json()["items"]} == {
        "approval.approve",
        "approval.reject",
    }
    assert audit.limits == [25, 25]


def test_activity_log_service_limits_sql_to_decision_actions(monkeypatch) -> None:
    import app.services.audit_service as audit_module

    calls: list[tuple[str, list]] = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, query, params) -> None:
            calls.append((query, params))

        def fetchall(self):
            return [{"audit_id": 17, "action": "approval.approve", "station_id": "S03"}]

    class FakeDatabase:
        @contextmanager
        def connection(self):
            yield object()

    monkeypatch.setattr(audit_module, "dict_cursor", lambda _connection: FakeCursor())
    rows = AuditService(FakeDatabase()).list_manager_activity_logs(limit=12)  # type: ignore[arg-type]

    assert rows == [{"audit_id": 17, "action": "approval.approve", "station_id": "S03"}]
    assert calls[0][1] == [list(MANAGER_ACTIVITY_LOG_ACTIONS), 12]
    assert "LEFT JOIN approval_requests" in calls[0][0]
    assert "WHERE audit.action = ANY(%s)" in calls[0][0]
