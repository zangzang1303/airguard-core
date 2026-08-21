from __future__ import annotations

import json

import httpx
import pytest
from pydantic import ValidationError

from src.agents.tools import BackendToolClient, FakeBackendToolClient
from src.agents.tools.contracts import (
    TOOL_REGISTRY,
    TOOL_REGISTRY_OWNER,
    TOOL_REGISTRY_VERSION,
    CurrentPm25Input,
    Pm25Forecast,
    Pm25ForecastInput,
    StationHistory,
    StationMeasurement,
    ToolError,
    ToolErrorCode,
    ToolName,
    UserProfile,
    WeatherContext,
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
async def test_fake_adapter_covers_all_mvp_stations():
    adapter = FakeBackendToolClient()

    results = [
        await adapter.get_current_pm25({"station_id": station_id}, request_id=f"req-{station_id}")
        for station_id in ("S01", "S02", "S03", "S04", "S05")
    ]

    assert all(result.ok for result in results)
    assert [result.data["station_id"] for result in results] == ["S01", "S02", "S03", "S04", "S05"]


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
async def test_active_alert_adapter_requests_only_active_backend_records():
    seen_query: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_query.update(dict(request.url.params))
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "alert_id": "alert-S01-active",
                        "station_id": "S01",
                        "alert_type": "pm25_threshold",
                        "severity": "warning",
                        "observed_value": 55.0,
                        "threshold_value": 50.0,
                        "status": "active",
                        "created_at": "2026-08-11T09:00:00+07:00",
                        "source": "backend_alert_rule:pm25-threshold-v1",
                    }
                ],
                "timestamp": "2026-08-11T09:00:01+07:00",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client)
        result = await adapter.get_active_alerts({"station_id": "S01"}, request_id="req-alerts")

    assert result.ok is True
    assert result.data["items"][0]["status"] == "active"
    assert seen_query == {"status": "active", "station_id": "S01"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "expected_code"),
    [
        (403, ToolErrorCode.PERMISSION_DENIED),
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
async def test_backend_adapter_rejects_current_without_explicit_freshness():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "station_id": "S01",
                "pm25": 999,
                "status": "online",
                "updated_at": "2026-08-04T09:00:00+07:00",
                "source": "simulator",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client)
        result = await adapter.get_current_pm25({"station_id": "S01"}, request_id="req-freshness")

    assert isinstance(result, ToolError)
    assert result.code == ToolErrorCode.SCHEMA_DRIFT


@pytest.mark.asyncio
async def test_backend_adapter_rejects_naive_environmental_timestamp():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "station_id": "S01",
                "pm25": 22.4,
                "status": "online",
                "is_stale": False,
                "updated_at": "2026-08-04T09:00:00",
                "source": "simulator",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client)
        result = await adapter.get_current_pm25({"station_id": "S01"}, request_id="req-timezone")

    assert isinstance(result, ToolError)
    assert result.code == ToolErrorCode.SCHEMA_DRIFT


@pytest.mark.asyncio
async def test_backend_adapter_maps_timeout_after_bounded_retries():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("backend read timed out", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client, max_retries=1)
        result = await adapter.get_current_pm25({"station_id": "S01"}, request_id="req-timeout")

    assert isinstance(result, ToolError)
    assert result.code == ToolErrorCode.TIMEOUT
    assert calls == 2


def test_environmental_contracts_require_grounding_metadata():
    with pytest.raises(ValidationError):
        StationMeasurement.model_validate(
            {
                "station_id": "S01",
                "pm25": 22.4,
                "status": "online",
                "updated_at": "2026-08-04T09:00:00+07:00",
                "source": "simulator",
            }
        )


def test_user_profile_accepts_backend_user_group_field():
    profile = UserProfile.model_validate(
        {"user_id": "demo-user", "role": "viewer", "user_group": "sensitive"}
    )

    assert profile.group == "sensitive"

    with pytest.raises(ValidationError):
        StationMeasurement.model_validate(
            {
                "station_id": "S01",
                "pm25": 22.4,
                "status": "online",
                "is_stale": False,
                "updated_at": "2026-08-04T09:00:00+07:00",
                "source": "official_monitor",
            }
        )

    with pytest.raises(ValidationError):
        WeatherContext.model_validate(
            {
                "area_id": "vinuni-ocean-park",
                "temperature": 31.5,
                "observed_at": "2026-08-04T09:00:00+07:00",
                "source": "fixture_weather",
            }
        )

    with pytest.raises(ValidationError):
        Pm25Forecast.model_validate(
            {
                "station_id": "S01",
                "is_stale": False,
                "items": [{"pm25": 25.0, "source": "fixture_forecast"}],
            }
        )

    with pytest.raises(ValidationError):
        Pm25Forecast.model_validate(
            {
                "station_id": "S01",
                "items": [{"hour": 1, "pm25": 25.0, "source": "fixture_forecast"}],
            }
        )


def test_history_contract_rejects_out_of_order_points():
    with pytest.raises(ValidationError):
        StationHistory.model_validate(
            {
                "station_id": "S01",
                "hours": 2,
                "items": [
                    {
                        "station_id": "S01",
                        "measured_at": "2026-08-04T09:00:00+07:00",
                        "pm25": 20,
                        "source": "simulator",
                    },
                    {
                        "station_id": "S01",
                        "measured_at": "2026-08-04T08:00:00+07:00",
                        "pm25": 19,
                        "source": "simulator",
                    },
                ],
            }
        )


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
                "is_stale": False,
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
    assert create_calls == ["/api/v1/proposals"]


@pytest.mark.asyncio
async def test_create_proposal_maps_backend_payload_header_and_response_id():
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["request_id"] = request.headers["x-request-id"]
        seen["idempotency_key"] = request.headers["idempotency-key"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(201, json={"request_id": "approval-123", "status": "pending"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://backend") as http_client:
        adapter = BackendToolClient("http://backend", client=http_client, max_retries=3)
        result = await adapter.create_warning_proposal(
            {
                "user_id": "demo-user",
                "idempotency_key": "alert-S02:policy-v1",
                "target": {"audience": "station_area", "station_id": "S02"},
                "action": "notify_station_area_users",
                "rationale": "Fresh PM2.5 and an active alert require manager review.",
                "policy_version": "policy-v1",
                "evidence": [
                    {
                        "source_tool": "get_current_pm25",
                        "station_id": "S02",
                        "observed_value": 58.2,
                        "source": "simulator",
                    },
                    {
                        "source_tool": "get_active_alerts",
                        "evidence_id": "alert-S02-001",
                        "station_id": "S02",
                        "threshold_value": 50,
                        "source": "backend_alert_rule:pm25-threshold-v1",
                    },
                ],
            },
            request_id="req-create-success",
        )

    assert result.ok is True
    assert result.data["proposal_id"] == "approval-123"
    assert result.data["status"] == "pending"
    assert seen == {
        "path": "/api/v1/proposals",
        "request_id": "req-create-success",
        "idempotency_key": "alert-S02:policy-v1",
        "body": {
            "request_type": "warning_proposal",
            "station_id": "S02",
            "proposed_action": "notify_station_area_users",
            "reason": "Fresh PM2.5 and an active alert require manager review.",
            "evidence": {
                "items": [
                    {
                        "aqi": None,
                        "aqi_category": None,
                        "pm25": None,
                        "co2": None,
                        "noise_db": None,
                        "temperature": None,
                        "source_tool": "get_current_pm25",
                        "evidence_id": None,
                        "station_id": "S02",
                        "aqi": None,
                        "aqi_category": None,
                        "pm25": None,
                        "co2": None,
                        "noise_db": None,
                        "temperature": None,
                        "observed_value": 58.2,
                        "threshold_value": None,
                        "measured_at": None,
                        "source": "simulator",
                        "rule_version": None,
                        "severity": None,
                    },
                    {
                        "aqi": None,
                        "aqi_category": None,
                        "pm25": None,
                        "co2": None,
                        "noise_db": None,
                        "temperature": None,
                        "source_tool": "get_active_alerts",
                        "evidence_id": "alert-S02-001",
                        "station_id": "S02",
                        "aqi": None,
                        "aqi_category": None,
                        "pm25": None,
                        "co2": None,
                        "noise_db": None,
                        "temperature": None,
                        "observed_value": None,
                        "threshold_value": 50.0,
                        "measured_at": None,
                        "source": "backend_alert_rule:pm25-threshold-v1",
                        "rule_version": None,
                        "severity": None,
                    },
                ],
                "target": {"audience": "station_area", "station_id": "S02"},
                "policy_version": "policy-v1",
                "requested_by": "demo-user",
                "expires_at": None,
            },
            "created_by": "ai_agent",
        },
    }

