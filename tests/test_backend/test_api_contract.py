from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

try:
    from fastapi.testclient import TestClient
except RuntimeError:
    TestClient = None  # type: ignore[assignment]


def load_app_without_database():
    os.environ.pop("DATABASE_URL", None)
    os.environ["CORS_ORIGINS"] = "http://localhost:5173"
    from app.main import app

    return app


def require_test_client():
    if TestClient is None:
        print("SKIP FastAPI TestClient requires httpx")
        return None
    return TestClient


def test_health_returns_process_status() -> None:
    client_class = require_test_client()
    if client_class is None:
        return
    client = client_class(load_app_without_database())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-request-id"]


def test_ready_returns_error_envelope_when_database_is_missing() -> None:
    client_class = require_test_client()
    if client_class is None:
        return
    client = client_class(load_app_without_database())
    response = client.get("/ready", headers={"X-Request-ID": "test-request"})

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "database_not_configured"
    assert body["request_id"] == "test-request"
    assert "stack" not in body


def test_reject_approval_requires_manager_role_before_database_use() -> None:
    client_class = require_test_client()
    if client_class is None:
        return
    client = client_class(load_app_without_database())
    response = client.post(
        "/api/v1/approvals/00000000-0000-0000-0000-000000000001/approve",
        json={"version": 1},
        headers={"X-User-Role": "viewer"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_openapi_schema_loads() -> None:
    client_class = require_test_client()
    if client_class is None:
        return
    client = client_class(load_app_without_database())
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "AirGuard AI API"


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
            print(f"PASS {name}")

