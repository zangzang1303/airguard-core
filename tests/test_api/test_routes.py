import pytest

import src.api.routes as agent_routes
from src.agents.graph import build_graph
from src.agents.policies.recommendations import RECOMMENDATION_POLICY_VERSION
from src.agents.tools.fake_adapter import FakeBackendToolClient


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_chat_empty_message(client):
    response = await client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_agent_status(client):
    response = await client.get("/api/v1/status")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_agent_chat_response_contract_and_correlation_id(client):
    response = await client.post(
        "/api/v1/agent/chat",
        json={"message": "Xin chào"},
        headers={"X-Request-ID": "api-contract-1"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == "api-contract-1"
    assert data["answer"] == data["response"]
    assert data["used_tools"] == []
    assert data["sources"] == []
    assert data["trace"]["intent"] == "greeting"


@pytest.mark.asyncio
async def test_agent_chat_passes_authenticated_user_and_station_context(client, monkeypatch):
    monkeypatch.setattr(agent_routes, "agent", build_graph(FakeBackendToolClient()))

    response = await client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Tôi có nên chạy bộ ngoài trời không?",
            "user_id": "demo-user",
            "station_id": "S02",
        },
        headers={"X-Request-ID": "api-recommendation-1"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == "api-recommendation-1"
    assert data["recommendation_policy_version"] == RECOMMENDATION_POLICY_VERSION
    assert data["trace"]["intent"] == "recommendation"
    assert "Quan sát tại S02" in data["answer"]
