from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

try:
    from fastapi.testclient import TestClient
except Exception as exc:
    raise AssertionError(f"FastAPI TestClient is required for API contract tests: {exc}")


def load_app_without_database():
    os.environ.pop("DATABASE_URL", None)
    os.environ["CORS_ORIGINS"] = "http://localhost:5173"
    import app.main as main_module
    return main_module


def test_health_returns_process_status() -> None:
    main_module = load_app_without_database()
    client = TestClient(main_module.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-request-id"]


def test_ready_returns_error_envelope_when_database_is_missing() -> None:
    main_module = load_app_without_database()
    client = TestClient(main_module.app)
    response = client.get("/ready", headers={"X-Request-ID": "test-request"})

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "database_not_configured"
    assert body["request_id"] == "test-request"
    assert "stack" not in body


def test_approval_requires_authentication_before_database_use() -> None:
    main_module = load_app_without_database()
    client = TestClient(main_module.app)
    response = client.post(
        "/api/v1/approvals/00000000-0000-0000-0000-000000000001/approve",
        json={"version": 1},
        headers={"X-User-Role": "viewer"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"


def test_openapi_schema_loads() -> None:
    main_module = load_app_without_database()
    client = TestClient(main_module.app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "AirGuard AI API"


# ── AI-24: Agent Chat Public Endpoint Resilience Contract ────────────────────

MOCK_PROFILE = {
    "user_id": "00000000-0000-0000-0000-000000000101",
    "role": "resident",
    "sensitivity_group": "normal",
}

MOCK_STATIONS = [
    {
        "station_id": "S03",
        "name": "S03 - VinUni",
        "status": "online",
        "freshness": "fresh",
        "aqi": 85,
        "source": "simulator",
        "updated_at": "2026-08-24T15:00:00Z",
    }
]

ENVIRONMENTAL_QUERY = "Chất lượng không khí và AQI hiện tại ở trạm S03 VinUni thế nào?"


def test_agent_chat_timeout_returns_structured_503_and_request_id_parity() -> None:
    """When Agent times out, public endpoint must return structured 503 with exact code and header parity."""
    from app.services.agent_service import AgentServiceError

    main_module = load_app_without_database()
    client = TestClient(main_module.app)

    mock_chat = AsyncMock(side_effect=AgentServiceError("agent_timeout", "Agent service timed out", 503))

    with patch.object(main_module.agent_service, "chat", new=mock_chat), \
         patch.object(main_module.user_service, "get_profile", return_value=MOCK_PROFILE), \
         patch.object(main_module.station_service, "list_stations", return_value=MOCK_STATIONS):
        response = client.post(
            "/api/v1/agent/chat",
            json={
                "message": ENVIRONMENTAL_QUERY,
                "user_id": "demo-user",
                "station_id": "S03",
            },
            headers={"X-Request-ID": "ai24-timeout-parity-test"},
        )

    assert response.status_code == 503
    body = response.json()

    assert body["code"] == "agent_timeout"
    assert "message" in body and isinstance(body["message"], str)
    assert body["request_id"] == "ai24-timeout-parity-test"
    assert "details" in body

    # Header parity
    assert response.headers.get("x-request-id") == body["request_id"]


def test_agent_chat_503_error_body_must_not_contain_answer_or_evidence_fields() -> None:
    """Error response for agent failure MUST NOT leak answer, evidence, sources, used_tools, map_actions, or proposal_id."""
    from app.services.agent_service import AgentServiceError

    main_module = load_app_without_database()
    client = TestClient(main_module.app)

    mock_chat = AsyncMock(side_effect=AgentServiceError("agent_unavailable", "Agent service is unavailable", 503))

    with patch.object(main_module.agent_service, "chat", new=mock_chat), \
         patch.object(main_module.user_service, "get_profile", return_value=MOCK_PROFILE), \
         patch.object(main_module.station_service, "list_stations", return_value=MOCK_STATIONS):
        response = client.post(
            "/api/v1/agent/chat",
            json={
                "message": ENVIRONMENTAL_QUERY,
                "user_id": "demo-user",
                "station_id": "S03",
            },
            headers={"X-Request-ID": "ai24-no-leak-test"},
        )

    assert response.status_code == 503
    body = response.json()

    forbidden = ["answer", "response", "evidence", "sources", "used_tools", "map_actions", "proposal_id"]
    present = [f for f in forbidden if f in body]
    assert not present, f"Error body MUST NOT contain: {', '.join(present)}"


def test_agent_chat_does_not_retry_on_timeout() -> None:
    """The public endpoint must not auto-retry; each POST triggers exactly one Agent call (assert_awaited_once)."""
    from app.services.agent_service import AgentServiceError

    main_module = load_app_without_database()
    client = TestClient(main_module.app)

    mock_chat = AsyncMock(side_effect=AgentServiceError("agent_timeout", "Agent service timed out", 503))

    with patch.object(main_module.agent_service, "chat", new=mock_chat) as mocked, \
         patch.object(main_module.user_service, "get_profile", return_value=MOCK_PROFILE), \
         patch.object(main_module.station_service, "list_stations", return_value=MOCK_STATIONS):
        response = client.post(
            "/api/v1/agent/chat",
            json={
                "message": ENVIRONMENTAL_QUERY,
                "user_id": "demo-user",
                "station_id": "S03",
            },
            headers={"X-Request-ID": "ai24-single-call-test"},
        )

    assert response.status_code == 503
    mocked.assert_awaited_once()


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
            print(f"PASS {name}")
