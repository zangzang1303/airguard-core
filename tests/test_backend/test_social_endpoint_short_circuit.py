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
    monkeypatch.setattr(main_module.geospatial_agent, "process_query", geospatial)

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
        "trace": {"intent": "current", "generation_mode": "deterministic_grounded"},
    }
    monkeypatch.setattr(main_module.agent_service, "chat", AsyncMock(return_value=agent_result))
    monkeypatch.setattr(
        main_module.user_service,
        "get_profile",
        Mock(return_value={"sensitivity_group": "normal"}),
    )
    monkeypatch.setattr(main_module.station_service, "list_stations", Mock(return_value=[]))
    monkeypatch.setattr(
        main_module.geospatial_agent,
        "process_query",
        Mock(
            return_value={
                "intent": "get_location_environment",
                "evidence": [],
                "map_actions": [{"type": "fly_to"}],
                "data_mode": "current",
            }
        ),
    )
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
    assert response["trace"]["map_intent"] == "get_location_environment"
