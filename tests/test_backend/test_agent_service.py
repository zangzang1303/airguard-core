from __future__ import annotations

import json

import httpx
import pytest

from backend.app.services.agent_service import AgentService, AgentServiceError


@pytest.mark.asyncio
async def test_agent_service_propagates_context_and_correlation_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/agent/chat"
        assert request.headers["X-Request-ID"] == "proxy-request-1"
        assert json.loads(request.read()) == {
            "message": "PM2.5 hiện tại thế nào?",
            "user_id": "demo-user",
            "station_id": "S03",
        }
        return httpx.Response(
            200,
            json={
                "answer": "grounded",
                "used_tools": ["get_current_pm25"],
                "sources": [{"tool_name": "get_current_pm25", "station_id": "S03"}],
                "request_id": "proxy-request-1",
                "trace": {"intent": "current"},
            },
        )

    service = AgentService("http://agent.test", transport=httpx.MockTransport(handler))
    result = await service.chat(
        message="PM2.5 hiện tại thế nào?",
        user_id="demo-user",
        station_id="S03",
        request_id="proxy-request-1",
    )

    assert result["answer"] == "grounded"


@pytest.mark.asyncio
async def test_agent_service_rejects_correlation_mismatch():
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            200,
            json={
                "answer": "grounded",
                "used_tools": [],
                "sources": [],
                "request_id": "wrong-request",
                "trace": {},
            },
        )
    )
    service = AgentService("http://agent.test", transport=transport)

    with pytest.raises(AgentServiceError) as exc_info:
        await service.chat(
            message="hello",
            user_id="demo-user",
            station_id=None,
            request_id="expected-request",
        )

    assert exc_info.value.code == "agent_correlation_mismatch"
