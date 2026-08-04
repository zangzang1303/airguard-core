import pytest


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
