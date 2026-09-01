from __future__ import annotations

import json

import httpx
import pytest

from backend.app.services.agent_service import AgentService, AgentServiceError


@pytest.mark.asyncio
async def test_agent_service_propagates_context_and_correlation_id():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/agent/chat"
        assert request.headers.get("X-Request-ID") == "proxy-request-1"
        data = json.loads(request.content)
        assert data == {
            "message": "Chất lượng không khí S03 thế nào?",
            "user_id": "demo-user",
            "station_id": "S03",
        }
        return httpx.Response(
            200,
            json={
                "answer": "Grounded response",
                "used_tools": ["get_current_pm25"],
                "sources": [{"tool_name": "get_current_pm25", "station_id": "S03", "source": "simulator"}],
                "request_id": "proxy-request-1",
                "trace": {"intent": "current"},
            },
        )

    service = AgentService("http://agent.test", transport=httpx.MockTransport(handler))
    result = await service.chat(
        message="Chất lượng không khí S03 thế nào?",
        user_id="demo-user",
        station_id="S03",
        request_id="proxy-request-1",
    )

    assert result["answer"] == "Grounded response"
    assert result["request_id"] == "proxy-request-1"


@pytest.mark.asyncio
async def test_agent_service_rejects_correlation_mismatch():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "answer": "grounded",
                "used_tools": [],
                "sources": [],
                "request_id": "wrong-request-id",
                "trace": {},
            },
        )

    service = AgentService("http://agent.test", transport=httpx.MockTransport(handler))

    with pytest.raises(AgentServiceError) as exc_info:
        await service.chat(
            message="Chất lượng không khí S03 thế nào?",
            user_id="demo-user",
            station_id=None,
            request_id="expected-request-id",
        )

    assert exc_info.value.code == "agent_correlation_mismatch"
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_agent_service_timeout_raises_agent_timeout():
    """Timeout from Agent service must map to agent_timeout, HTTP 503."""
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Simulated timeout", request=request)

    service = AgentService("http://agent.test", transport=httpx.MockTransport(handler))

    with pytest.raises(AgentServiceError) as exc_info:
        await service.chat(
            message="AQI hiện tại ở S03 là bao nhiêu?",
            user_id="demo-user",
            station_id="S03",
            request_id="timeout-req-1",
        )

    assert exc_info.value.code == "agent_timeout"
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_agent_service_network_error_raises_agent_unavailable():
    """Network/connection failure must map to agent_unavailable, HTTP 503."""
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Simulated connection refused", request=request)

    service = AgentService("http://agent.test", transport=httpx.MockTransport(handler))

    with pytest.raises(AgentServiceError) as exc_info:
        await service.chat(
            message="AQI hiện tại ở S03 là bao nhiêu?",
            user_id="demo-user",
            station_id="S03",
            request_id="network-req-1",
        )

    assert exc_info.value.code == "agent_unavailable"
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_agent_service_upstream_503_raises_agent_unavailable():
    """Upstream Agent returning 503 must map to agent_unavailable, HTTP 503."""
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "agent_overloaded"})

    service = AgentService("http://agent.test", transport=httpx.MockTransport(handler))

    with pytest.raises(AgentServiceError) as exc_info:
        await service.chat(
            message="AQI hiện tại ở S03?",
            user_id="demo-user",
            station_id="S03",
            request_id="upstream-503-req-1",
        )

    assert exc_info.value.code == "agent_unavailable"
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_agent_service_invalid_json_raises_schema_drift():
    """Non-JSON upstream response must map to agent_schema_drift, HTTP 503."""
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json", headers={"Content-Type": "text/plain"})

    service = AgentService("http://agent.test", transport=httpx.MockTransport(handler))

    with pytest.raises(AgentServiceError) as exc_info:
        await service.chat(
            message="AQI hiện tại ở S03?",
            user_id="demo-user",
            station_id="S03",
            request_id="invalid-json-req-1",
        )

    assert exc_info.value.code == "agent_schema_drift"
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_agent_service_missing_required_fields_raises_schema_drift():
    """HTTP 200 response missing required fields must raise agent_schema_drift."""
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"answer": "some answer"})

    service = AgentService("http://agent.test", transport=httpx.MockTransport(handler))

    with pytest.raises(AgentServiceError) as exc_info:
        await service.chat(
            message="AQI hiện tại?",
            user_id="demo-user",
            station_id=None,
            request_id="missing-fields-req-1",
        )

    assert exc_info.value.code == "agent_schema_drift"
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_agent_service_does_not_auto_retry():
    """POST chat proxy must make exactly one request; no automatic retry on failure."""
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        raise httpx.ConnectError("Simulated failure", request=request)

    service = AgentService("http://agent.test", transport=httpx.MockTransport(handler))

    with pytest.raises(AgentServiceError):
        await service.chat(
            message="test message",
            user_id="demo-user",
            station_id=None,
            request_id="no-retry-req-1",
        )

    assert call_count == 1, f"Expected exactly 1 call, got {call_count} (auto-retry detected)"
