from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest
from starlette.requests import Request

from backend.app import main as main_module


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
    monkeypatch.setattr(main_module.agent_service, "chat", agent_chat)
    monkeypatch.setattr(main_module.user_service, "get_profile", profile)
    monkeypatch.setattr(main_module.station_service, "list_stations", stations)
    monkeypatch.setattr(main_module.geospatial_agent, "plan_map_actions", geospatial)

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
    agent_chat.assert_not_called()
    profile.assert_not_called()
    stations.assert_not_called()
    geospatial.assert_not_called()


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
    assert response["trace"]["map_planner_status"] == "skipped"
    assert response["trace"]["map_planner_reason"] == "non_spatial_intent"
    agent_chat.assert_awaited_once()
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
    agent_chat.assert_awaited_once()
    planner.assert_called_once()
    assert planner.call_args.kwargs["authoritative_agent_result"] is agent_result


@pytest.mark.asyncio
async def test_map_planner_failure_preserves_grounded_spatial_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
