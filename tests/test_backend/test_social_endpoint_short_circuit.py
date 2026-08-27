from __future__ import annotations

from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from starlette.requests import Request

from backend.app import main as main_module

_CONVERSATION_ID = "11111111-1111-4111-8111-111111111111"


def _mock_conversation_memory(
    monkeypatch: pytest.MonkeyPatch,
    *,
    context: dict | None = None,
    record_result: object | None = None,
) -> tuple[Mock, Mock]:
    start = Mock(
        return_value={
            "conversation_id": _CONVERSATION_ID,
            "context": context
            or {"context_version": 1, "station_ids": [], "turn_count": 0},
        }
    )
    record = Mock(return_value=record_result or {"turn_count": 1})
    monkeypatch.setattr(main_module.conversation_memory_service, "start_or_resume", start)
    monkeypatch.setattr(
        main_module.conversation_memory_service,
        "record_agent_result",
        record,
    )
    return start, record


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("message", "kind"),
    [
        ("Cảm ơn bạn nhé.", "acknowledgement"),
        ("Bạn có thể giúp gì cho tôi?", "capabilities"),
        ("Bạn\u00a0có khỏe không...", "wellbeing"),
        ("Hôm nay bạn thế nào?", "wellbeing"),
    ],
)
async def test_public_social_endpoint_short_circuits_all_downstream_services(
    monkeypatch: pytest.MonkeyPatch,
    message: str,
    kind: str,
) -> None:
    agent_chat = AsyncMock(side_effect=AssertionError("Agent downstream must not be called"))
    profile = Mock(side_effect=AssertionError("Profile lookup must not be called"))
    stations = Mock(side_effect=AssertionError("Station lookup must not be called"))
    geospatial = Mock(side_effect=AssertionError("Geospatial planner must not be called"))
    memory = Mock(side_effect=AssertionError("Social reply must not access conversation storage"))
    monkeypatch.setattr(main_module.agent_service, "chat", agent_chat)
    monkeypatch.setattr(main_module.user_service, "get_profile", profile)
    monkeypatch.setattr(main_module.station_service, "list_stations", stations)
    monkeypatch.setattr(main_module.geospatial_agent, "plan_map_actions", geospatial)
    monkeypatch.setattr(main_module.conversation_memory_service, "start_or_resume", memory)

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/agent/chat",
            "headers": [(b"x-request-id", b"session-3e-public-unit")],
        }
    )
    body = main_module.AgentChatRequest(
        message=message,
        user_id="demo-user",
        station_id="S03",
        map_context={"selected_sensor": "S03"},
    )

    response = await main_module.agent_chat(request, body, None)

    assert response["intent"] == "social"
    assert response["conversation_kind"] == kind
    assert response["used_tools"] == []
    assert response["tool_arguments"] == []
    assert response["sources"] == []
    assert response["map_actions"] == []
    assert response["proposal_id"] is None
    assert response["trace"]["generation_mode"] == "deterministic_grounded"
    assert response["trace"]["conversation_mode"] == "deterministic_social"
    assert str(UUID(response["conversation_id"])) == response["conversation_id"]
    agent_chat.assert_not_called()
    profile.assert_not_called()
    stations.assert_not_called()
    geospatial.assert_not_called()
    memory.assert_not_called()


@pytest.mark.asyncio
async def test_public_domain_response_preserves_canonical_agent_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent_result = {
        "answer": "Grounded S03 answer",
        "intent": "current",
        "conversation_kind": None,
        "used_tools": ["get_current_pm25"],
        "tool_arguments": [{"station_id": "S03"}],
        "sources": [
            {
                "tool_name": "get_current_pm25",
                "station_id": "S03",
                "observed_at": "2026-08-24T14:00:00Z",
                "source": "simulator",
            }
        ],
        "proposal_id": None,
        "outcome": "answered",
        "trace": {
            "intent": "current",
            "final_outcome": "answered",
            "generation_mode": "deterministic_grounded",
        },
    }
    agent_chat = AsyncMock(return_value=agent_result)
    profile = Mock(side_effect=AssertionError("Non-spatial query must not load a profile"))
    stations = Mock(side_effect=AssertionError("Non-spatial query must not load all stations"))
    geospatial = Mock(side_effect=AssertionError("Non-spatial query must not run map planning"))
    _, record_memory = _mock_conversation_memory(
        monkeypatch,
        context={
            "context_version": 1,
            "station_ids": ["S02"],
            "primary_station_id": "S02",
            "turn_count": 1,
        },
        record_result={"turn_count": 2},
    )
    monkeypatch.setattr(main_module.agent_service, "chat", agent_chat)
    monkeypatch.setattr(main_module.user_service, "get_profile", profile)
    monkeypatch.setattr(main_module.station_service, "list_stations", stations)
    monkeypatch.setattr(main_module.geospatial_agent, "plan_map_actions", geospatial)
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/agent/chat",
            "headers": [(b"x-request-id", b"session-3e-domain-unit")],
        }
    )
    body = main_module.AgentChatRequest(
        message="Cảm ơn, AQI S03 hiện tại thế nào?",
        user_id="demo-user",
        station_id="S01",
    )

    response = await main_module.agent_chat(request, body, None)

    assert response["intent"] == "current"
    assert response["tool_arguments"] == [{"station_id": "S03"}]
    assert response["sources"][0]["station_id"] == "S03"
    assert response["evidence"] == response["sources"]
    assert response["map_actions"] == []
    assert response["conversation_id"] == _CONVERSATION_ID
    assert response["trace"]["memory_persisted"] is True
    assert response["trace"]["memory_context_used"] is True
    assert response["trace"]["map_planner_status"] == "skipped"
    assert response["trace"]["map_planner_reason"] == "non_spatial_intent"
    agent_chat.assert_awaited_once()
    assert agent_chat.await_args.kwargs["conversation_context"]["station_ids"] == ["S02"]
    record_memory.assert_called_once()
    profile.assert_not_called()
    stations.assert_not_called()
    geospatial.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "outcome",
    ["insufficient_data", "clarification", "refused", "direct_response"],
)
async def test_terminal_agent_outcome_never_runs_map_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
) -> None:
    _mock_conversation_memory(monkeypatch)
    agent_result = {
        "answer": "Canonical terminal answer",
        "intent": "spatial",
        "used_tools": [],
        "tool_arguments": [],
        "sources": [],
        "outcome": outcome,
        "trace": {"intent": "spatial", "final_outcome": outcome},
    }
    profile = Mock(side_effect=AssertionError("Terminal outcome must not load a profile"))
    stations = Mock(side_effect=AssertionError("Terminal outcome must not load stations"))
    geospatial = Mock(side_effect=AssertionError("Terminal outcome must not run map planning"))
    monkeypatch.setattr(
        main_module.agent_service,
        "chat",
        AsyncMock(return_value=agent_result),
    )
    monkeypatch.setattr(main_module.user_service, "get_profile", profile)
    monkeypatch.setattr(main_module.station_service, "list_stations", stations)
    monkeypatch.setattr(main_module.geospatial_agent, "plan_map_actions", geospatial)

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/agent/chat",
            "headers": [(b"x-request-id", b"terminal-map-gate")],
        }
    )
    body = main_module.AgentChatRequest(
        message="So sánh khu Sapphire với Hồ Ngọc Trai",
        user_id="demo-user",
    )

    response = await main_module.agent_chat(request, body, None)

    assert response["response"] == "Canonical terminal answer"
    assert response["map_actions"] == []
    assert response["trace"]["map_planner_status"] == "skipped"
    assert response["trace"]["map_planner_reason"] == f"agent_{outcome}"
    profile.assert_not_called()
    stations.assert_not_called()
    geospatial.assert_not_called()


@pytest.mark.asyncio
async def test_spatial_answer_without_validated_source_skips_map_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_conversation_memory(monkeypatch)
    agent_result = {
        "answer": "Spatial answer without usable evidence",
        "intent": "spatial",
        "used_tools": ["get_spatial_air_quality"],
        "tool_arguments": [{"metric": "aqi", "forecast_hour": 0}],
        "sources": [],
        "outcome": "answered",
        "trace": {"intent": "spatial", "final_outcome": "answered"},
    }
    profile = Mock(side_effect=AssertionError("Source gate must run before profile lookup"))
    stations = Mock(side_effect=AssertionError("Source gate must run before station lookup"))
    planner = Mock(side_effect=AssertionError("Missing source must skip map planning"))
    monkeypatch.setattr(
        main_module.agent_service,
        "chat",
        AsyncMock(return_value=agent_result),
    )
    monkeypatch.setattr(main_module.user_service, "get_profile", profile)
    monkeypatch.setattr(main_module.station_service, "list_stations", stations)
    monkeypatch.setattr(main_module.geospatial_agent, "plan_map_actions", planner)

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/agent/chat",
            "headers": [(b"x-request-id", b"spatial-source-gate")],
        }
    )
    response = await main_module.agent_chat(
        request,
        main_module.AgentChatRequest(
            message="So sánh chất lượng không khí toàn khu",
            user_id="demo-user",
        ),
        None,
    )

    assert response["response"] == "Spatial answer without usable evidence"
    assert response["map_actions"] == []
    assert response["trace"]["map_planner_status"] == "skipped"
    assert response["trace"]["map_planner_reason"] == "missing_validated_spatial_source"
    profile.assert_not_called()
    stations.assert_not_called()
    planner.assert_not_called()


@pytest.mark.asyncio
async def test_spatial_answer_runs_ui_only_map_planner_after_source_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_conversation_memory(monkeypatch)
    spatial_source = {
        "tool_name": "get_spatial_air_quality",
        "observed_at": "2026-08-27T08:00:00Z",
        "source": "spatial_idw_dispersion_model",
    }
    agent_result = {
        "answer": "Canonical spatial answer",
        "answer_summary": "Canonical spatial summary",
        "intent": "spatial",
        "used_tools": ["get_spatial_air_quality"],
        "tool_arguments": [{"metric": "aqi", "forecast_hour": 0}],
        "sources": [spatial_source],
        "outcome": "answered",
        "trace": {"intent": "spatial", "final_outcome": "answered"},
    }
    agent_chat = AsyncMock(return_value=agent_result)
    planner = Mock(
        return_value={
            "map_actions": [{"type": "fly_to", "lat": 20.99, "lng": 105.94}],
            "map_intent": "recommend_running_route",
            "data_mode": "current",
        }
    )
    monkeypatch.setattr(main_module.agent_service, "chat", agent_chat)
    monkeypatch.setattr(
        main_module.user_service,
        "get_profile",
        Mock(return_value={"sensitivity_group": "normal"}),
    )
    monkeypatch.setattr(
        main_module.station_service,
        "list_stations",
        Mock(return_value=[{"station_id": "S01"}]),
    )
    monkeypatch.setattr(main_module.geospatial_agent, "plan_map_actions", planner)

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/agent/chat",
            "headers": [(b"x-request-id", b"spatial-map-gate")],
        }
    )
    body = main_module.AgentChatRequest(
        message="Gợi ý cung đường chạy bộ ít ô nhiễm nhất",
        user_id="demo-user",
    )

    response = await main_module.agent_chat(request, body, None)

    assert response["answer"] == {
        "summary": "Canonical spatial summary",
        "details": "",
    }
    assert response["response"] == "Canonical spatial answer"
    assert response["intent"] == "spatial"
    assert response["sources"] == [spatial_source]
    assert response["evidence"] == [spatial_source]
    assert response["map_actions"] == [
        {"type": "fly_to", "lat": 20.99, "lng": 105.94}
    ]
    assert response["trace"]["map_planner_status"] == "completed"
    assert response["trace"]["map_intent"] == "recommend_running_route"
    assert response["map_intent"] == "recommend_running_route"
    agent_chat.assert_awaited_once()
    planner.assert_called_once()
    assert planner.call_args.kwargs["authoritative_agent_result"] is agent_result


@pytest.mark.asyncio
async def test_compare_answer_projects_validated_stations_without_changing_intent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_conversation_memory(monkeypatch)
    sources = [
        {
            "tool_name": "compare_stations",
            "station_id": station_id,
            "observed_at": "2026-08-27T08:00:00Z",
            "source": "simulator",
        }
        for station_id in ("S01", "S02")
    ]
    agent_result = {
        "answer": "Canonical S01/S02 comparison",
        "intent": "compare",
        "used_tools": ["compare_stations"],
        "tool_arguments": [{"station_ids": ["S01", "S02"]}],
        "sources": sources,
        "outcome": "answered",
        "trace": {"intent": "compare", "final_outcome": "answered"},
    }
    locations = [
        {
            "station_id": "S01",
            "station_name": "Trục Đa Tốn",
            "latitude": 21.0008,
            "longitude": 105.9428,
        },
        {
            "station_id": "S02",
            "station_name": "Khu Sapphire",
            "latitude": 20.9975,
            "longitude": 105.943,
        },
    ]
    location_lookup = Mock(return_value=locations)
    monkeypatch.setattr(
        main_module.agent_service,
        "chat",
        AsyncMock(return_value=agent_result),
    )
    monkeypatch.setattr(
        main_module.station_service,
        "get_station_locations",
        location_lookup,
    )

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/agent/chat",
            "headers": [(b"x-request-id", b"compare-map-projection")],
        }
    )
    response = await main_module.agent_chat(
        request,
        main_module.AgentChatRequest(
            message="So sánh S01 và S02 hiện tại",
            user_id="demo-user",
        ),
        None,
    )

    assert response["intent"] == "compare"
    assert response["map_intent"] == "compare_stations"
    assert response["sources"] == sources
    assert [
        action["sensor_id"]
        for action in response["map_actions"]
        if action["type"] == "highlight_sensor"
    ] == ["S01", "S02"]
    assert response["trace"]["map_planner_status"] == "completed"
    location_lookup.assert_called_once_with(["S01", "S02"])


@pytest.mark.asyncio
async def test_map_planner_failure_preserves_grounded_spatial_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_conversation_memory(monkeypatch)
    agent_result = {
        "answer": "Grounded spatial answer remains available",
        "intent": "spatial",
        "used_tools": ["get_spatial_air_quality"],
        "tool_arguments": [{"metric": "aqi", "forecast_hour": 0}],
        "sources": [
            {
                "tool_name": "get_spatial_air_quality",
                "observed_at": "2026-08-27T08:00:00Z",
                "source": "spatial_idw_dispersion_model",
            }
        ],
        "outcome": "answered",
        "trace": {"intent": "spatial", "final_outcome": "answered"},
    }
    monkeypatch.setattr(
        main_module.agent_service,
        "chat",
        AsyncMock(return_value=agent_result),
    )
    monkeypatch.setattr(
        main_module.user_service,
        "get_profile",
        Mock(return_value={"sensitivity_group": "normal"}),
    )
    monkeypatch.setattr(
        main_module.station_service,
        "list_stations",
        Mock(return_value=[{"station_id": "S01"}]),
    )
    monkeypatch.setattr(
        main_module.geospatial_agent,
        "plan_map_actions",
        Mock(
            side_effect=main_module.ServiceError(
                "insufficient_geospatial_station_data",
                "not enough stations",
                503,
            )
        ),
    )

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/agent/chat",
            "headers": [(b"x-request-id", b"spatial-planner-failure")],
        }
    )
    response = await main_module.agent_chat(
        request,
        main_module.AgentChatRequest(
            message="Gợi ý cung đường chạy bộ ít ô nhiễm nhất",
            user_id="demo-user",
        ),
        None,
    )

    assert response["response"] == "Grounded spatial answer remains available"
    assert response["map_actions"] == []
    assert response["trace"]["map_planner_status"] == "unavailable"
    assert (
        response["trace"]["map_planner_reason"]
        == "insufficient_geospatial_station_data"
    )


@pytest.mark.asyncio
async def test_memory_write_failure_preserves_grounded_agent_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent_result = {
        "answer": "Grounded S03 answer remains available",
        "intent": "current",
        "outcome": "answered",
        "used_tools": ["get_current_pm25"],
        "tool_arguments": [{"station_id": "S03"}],
        "sources": [
            {
                "tool_name": "get_current_pm25",
                "station_id": "S03",
                "source": "simulator",
            }
        ],
        "trace": {"intent": "current", "final_outcome": "answered"},
    }
    start = Mock(
        return_value={
            "conversation_id": _CONVERSATION_ID,
            "context": {"context_version": 1, "station_ids": [], "turn_count": 0},
        }
    )
    record = Mock(
        side_effect=main_module.ServiceError(
            "conversation_memory_unavailable",
            "memory write failed",
            503,
        )
    )
    profile = Mock(side_effect=AssertionError("Non-spatial query must not load a profile"))
    stations = Mock(side_effect=AssertionError("Non-spatial query must not load all stations"))
    planner = Mock(side_effect=AssertionError("Non-spatial query must not run map planning"))
    monkeypatch.setattr(main_module.conversation_memory_service, "start_or_resume", start)
    monkeypatch.setattr(main_module.conversation_memory_service, "record_agent_result", record)
    monkeypatch.setattr(main_module.agent_service, "chat", AsyncMock(return_value=agent_result))
    monkeypatch.setattr(main_module.user_service, "get_profile", profile)
    monkeypatch.setattr(main_module.station_service, "list_stations", stations)
    monkeypatch.setattr(main_module.geospatial_agent, "plan_map_actions", planner)

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/agent/chat",
            "headers": [(b"x-request-id", b"memory-write-failure")],
        }
    )
    response = await main_module.agent_chat(
        request,
        main_module.AgentChatRequest(
            message="AQI S03 hiện tại thế nào?",
            user_id="demo-user",
            station_id="S03",
        ),
        None,
    )

    assert response["response"] == "Grounded S03 answer remains available"
    assert response["map_actions"] == []
    assert response["trace"]["memory_persisted"] is False
    assert response["trace"]["memory_failure_reason"] == "conversation_memory_unavailable"
    profile.assert_not_called()
    stations.assert_not_called()
    planner.assert_not_called()
