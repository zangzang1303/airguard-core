from __future__ import annotations

import re
import pytest

from src.agents.graph import agent, build_graph
from src.agents.response_composer import INSUFFICIENT_DATA_MESSAGE
from src.agents.tools.contracts import ToolError, ToolErrorCode, ToolName
from src.agents.tools.fake_adapter import FakeBackendToolClient


class TimeoutBackendToolClient(FakeBackendToolClient):
    """Tool client adapter where environmental tools fail with ToolErrorCode.TIMEOUT."""

    async def get_current_pm25(self, payload, request_id="fixture-request"):
        return ToolError(
            tool_name=ToolName.GET_CURRENT_PM25,
            code=ToolErrorCode.TIMEOUT,
            message="Backend request timed out after deadline",
            request_id=request_id,
            status_code=503,
        )

    async def get_station_history(self, payload, request_id="fixture-request"):
        return ToolError(
            tool_name=ToolName.GET_STATION_HISTORY,
            code=ToolErrorCode.TIMEOUT,
            message="Backend request timed out after deadline",
            request_id=request_id,
            status_code=503,
        )

    async def compare_stations(self, payload, request_id="fixture-request"):
        return ToolError(
            tool_name=ToolName.COMPARE_STATIONS,
            code=ToolErrorCode.TIMEOUT,
            message="Backend request timed out after deadline",
            request_id=request_id,
            status_code=503,
        )

    async def get_weather_context(self, payload, request_id="fixture-request"):
        return ToolError(
            tool_name=ToolName.GET_WEATHER_CONTEXT,
            code=ToolErrorCode.TIMEOUT,
            message="Backend request timed out after deadline",
            request_id=request_id,
            status_code=503,
        )

    async def get_pm25_forecast(self, payload, request_id="fixture-request"):
        return ToolError(
            tool_name=ToolName.GET_PM25_FORECAST,
            code=ToolErrorCode.TIMEOUT,
            message="Backend request timed out after deadline",
            request_id=request_id,
            status_code=503,
        )

    async def get_active_alerts(self, payload, request_id="fixture-request"):
        return ToolError(
            tool_name=ToolName.GET_ACTIVE_ALERTS,
            code=ToolErrorCode.TIMEOUT,
            message="Backend request timed out after deadline",
            request_id=request_id,
            status_code=503,
        )

    async def get_user_profile(self, payload, request_id="fixture-request"):
        return ToolError(
            tool_name=ToolName.GET_USER_PROFILE,
            code=ToolErrorCode.TIMEOUT,
            message="Backend request timed out after deadline",
            request_id=request_id,
            status_code=503,
        )


@pytest.mark.asyncio
async def test_agent_basic_flow():
    result = await agent.ainvoke({"query": "Hello", "request_id": "test-req-1"})
    assert "response" in result


@pytest.mark.asyncio
async def test_agent_state_structure():
    result = await agent.ainvoke({"query": "Test query", "request_id": "test-req-2"})
    assert isinstance(result, dict)
    assert "query" in result


@pytest.mark.asyncio
async def test_agent_backend_timeout_fails_closed_no_grounded_claim():
    """
    AI-24 Agent Graph Resilience Test:
    When backend tools time out (ToolErrorCode.TIMEOUT / backend_timeout), the Agent must:
      - Fail closed with outcome='insufficient_data'
      - Return sources=[] (no fake provenance)
      - Return proposal_id=None (no hallucinated actions)
      - Never fabricate AQI, PM2.5, sensor values, or timestamps.
    """
    graph = build_graph(tool_client=TimeoutBackendToolClient())

    result = await graph.ainvoke({
        "query": "Chất lượng không khí và AQI hiện tại ở trạm S03 VinUni thế nào?",
        "user_id": "demo-user",
        "station_id": "S03",
        "request_id": "ai24-agent-timeout-test",
    })

    assert isinstance(result, dict), "Result must be a dict"

    # Outcome check
    outcome = result.get("outcome") or result.get("trace", {}).get("final_outcome")
    assert outcome == "insufficient_data", f"Expected outcome='insufficient_data', got: {outcome}"

    # Sources must be empty
    sources = result.get("sources", [])
    assert isinstance(sources, list), "sources must be a list"
    assert len(sources) == 0, f"sources must be empty on timeout, got: {sources}"

    # Proposal ID must be None
    assert result.get("proposal_id") is None, "proposal_id must be None on tool timeout"

    # Answer text verification
    answer_text = ""
    answer = result.get("answer", "")
    if isinstance(answer, dict):
        answer_text = (answer.get("summary", "") or "") + " " + (answer.get("details", "") or "")
    elif isinstance(answer, str):
        answer_text = answer
    response_text = result.get("response", "") or ""
    full_text = (answer_text + " " + response_text).lower()

    # Must contain insufficient data message
    assert INSUFFICIENT_DATA_MESSAGE.lower() in full_text or "không đủ dữ liệu" in full_text

    # Must NOT contain numeric environmental claims
    grounded_numeric_pattern = re.compile(r"(aqi|pm2\.5|pm25|co2|noise)\s*[=:]\s*\d+")
    assert not grounded_numeric_pattern.search(full_text), (
        f"Agent must NOT produce grounded numeric claims when tools time out. Found in: '{full_text[:300]}'"
    )
