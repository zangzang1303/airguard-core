from __future__ import annotations

import httpx
import pytest
from pydantic import ValidationError

from src.agents.tools import BackendToolClient, FakeBackendToolClient
from src.agents.tools.contracts import (
    TOOL_REGISTRY,
    TOOL_REGISTRY_OWNER,
    TOOL_REGISTRY_VERSION,
    CurrentPm25Input,
    Pm25ForecastInput,
    ToolError,
    ToolErrorCode,
    ToolName,
)


def test_tool_registry_has_all_required_tools():
    assert TOOL_REGISTRY_VERSION
    assert TOOL_REGISTRY_OWNER == "ai-agent"
    assert set(TOOL_REGISTRY) == {
        ToolName.GET_CURRENT_PM25,
        ToolName.GET_STATION_HISTORY,
        ToolName.COMPARE_STATIONS,
        ToolName.GET_WEATHER_CONTEXT,
        ToolName.GET_PM25_FORECAST,
        ToolName.GET_ACTIVE_ALERTS,
        ToolName.GET_USER_PROFILE,
        ToolName.CREATE_WARNING_PROPOSAL,
    }


def test_tool_input_validation_station_and_hours():
    assert CurrentPm25Input(station_id="s01").station_id == "S01"
    assert Pm25ForecastInput(station_id="S01", hours=3).hours == 3
    with pytest.raises(ValidationError):
        CurrentPm25Input(station_id="S99")
    with pytest.raises(ValidationError):
        Pm25ForecastInput(station_id="S01", hours=4)


@pytest.mark.asyncio
async def test_fake_adapter_validates_without_llm_or_db():
    adapter = FakeBackendToolClient()

    current = await adapter.get_current_pm25({"station_id": "S01"}, request_id="req-1")
    assert current.ok is True
    assert current.data["station_id"] == "S01"
    assert current.data["source"] == "simulator"

    invalid = await adapter.get_station_history({"station_id": "S01", "hours": 73}, request_id="req-2")
    assert isinstance(invalid, ToolError)
    assert invalid.code == ToolErrorCode.VALIDATION_ERROR


@pytest.mark.asyncio
async def test_backend_adapter_maps_success_and_request_id_header():
    seen_headers = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers["x-request-id"])
        return httpx.Response(
            200,
            json={
                "station_id": "S01",
                "station_name": "VinUni Gate",
                "latitude": 20.0,
                "longitude": 105.0,
                "pm25": 22.4,
                "status": "online",
                "level": "good",
                "is_stale": False,
                "updated_at": "2026-08-04T09:00:00+07:00",
                "source": "simulator",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client)
        result = await adapter.get_current_pm25({"station_id": "S01"}, request_id="req-success")

    assert result.ok is True
    assert result.data["pm25"] == 22.4
    assert seen_headers == ["req-success"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "expected_code"),
    [
        (404, ToolErrorCode.NOT_FOUND),
        (422, ToolErrorCode.VALIDATION_ERROR),
        (503, ToolErrorCode.UNAVAILABLE),
    ],
)
async def test_backend_adapter_maps_http_errors(status_code, expected_code):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"message": "backend says no"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client, max_retries=0)
        result = await adapter.get_current_pm25({"station_id": "S01"}, request_id="req-error")

    assert isinstance(result, ToolError)
    assert result.code == expected_code
    assert result.status_code == status_code


@pytest.mark.asyncio
async def test_backend_adapter_maps_malformed_json():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client)
        result = await adapter.get_current_pm25({"station_id": "S01"}, request_id="req-json")

    assert isinstance(result, ToolError)
    assert result.code == ToolErrorCode.MALFORMED_RESPONSE


@pytest.mark.asyncio
async def test_backend_adapter_maps_schema_drift():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"station_id": "S01", "pm25": 22.4})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client)
        result = await adapter.get_current_pm25({"station_id": "S01"}, request_id="req-drift")

    assert isinstance(result, ToolError)
    assert result.code == ToolErrorCode.SCHEMA_DRIFT


@pytest.mark.asyncio
async def test_backend_adapter_retries_get_but_not_create_proposal():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if len(calls) == 1:
            return httpx.Response(503, json={"message": "temporary outage"})
        return httpx.Response(
            200,
            json={
                "station_id": "S01",
                "pm25": 22.4,
                "status": "online",
                "updated_at": "2026-08-04T09:00:00+07:00",
                "source": "simulator",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client, max_retries=1)
        result = await adapter.get_current_pm25({"station_id": "S01"}, request_id="req-retry")

    assert result.ok is True
    assert calls == ["/api/v1/stations/S01/current", "/api/v1/stations/S01/current"]

    create_calls = []

    def create_handler(request: httpx.Request) -> httpx.Response:
        create_calls.append(request.url.path)
        return httpx.Response(503, json={"message": "create outage"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(create_handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client, max_retries=3)
        result = await adapter.create_warning_proposal(
            {
                "user_id": "demo-user",
                "idempotency_key": "proposal-key-1",
                "target": {"audience": "station_area", "station_id": "S01"},
                "action": "Notify station area users",
                "rationale": "PM2.5 threshold evidence requires manager review.",
                "policy_version": "policy-test",
                "evidence": [{"source_tool": "get_current_pm25", "station_id": "S01", "observed_value": 52.0}],
            },
            request_id="req-create",
        )

    assert isinstance(result, ToolError)
    assert create_calls == ["/api/v1/warning-proposals"]

