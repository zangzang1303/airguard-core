from __future__ import annotations

from copy import deepcopy

import pytest

from src.agents.graph import build_graph
from src.agents.policies.recommendations import RECOMMENDATION_POLICY_VERSION, build_recommendation
from src.agents.response_composer import INSUFFICIENT_DATA_MESSAGE
from src.agents.tools.fake_adapter import DEFAULT_FIXTURES, FakeBackendToolClient


def _forecast(station_id: str = "S02") -> dict:
    return {
        "station_id": station_id,
        "items": [
            {"hour": 1, "pm25": 61.0, "confidence": 0.7, "source": "fixture_forecast"},
            {"hour": 2, "pm25": 64.0, "confidence": 0.7, "source": "fixture_forecast"},
            {"hour": 3, "pm25": 68.0, "confidence": 0.7, "source": "fixture_forecast"},
        ],
        "generated_at": "2026-08-08T10:00:00+07:00",
        "model_name": "fixture-baseline-v1",
        "freshness": "fresh",
    }


@pytest.mark.parametrize(
    ("group", "expected_action"),
    [
        ("normal", "giảm hoạt động ngoài trời"),
        ("sensitive", "tránh hoạt động ngoài trời"),
        ("outdoor_sport", "hoãn buổi tập ngoài trời"),
    ],
)
def test_same_environment_produces_group_specific_recommendations(group, expected_action):
    decision, assessment = build_recommendation(
        current=deepcopy(DEFAULT_FIXTURES["current"]["S02"]),
        alerts=deepcopy(DEFAULT_FIXTURES["alerts"]),
        forecast=_forecast(),
        profile={"user_id": "profile-user", "group": group},
    )

    assert expected_action in decision.action
    assert decision.user_group == group
    assert decision.has_active_alert is True
    assert decision.policy_version == RECOMMENDATION_POLICY_VERSION
    assert assessment.station_id == "S02"


@pytest.mark.parametrize("group", [None, "unknown", "children"])
def test_recommendation_does_not_guess_missing_or_unknown_group(group):
    with pytest.raises(ValueError, match="backend user group"):
        build_recommendation(
            current=deepcopy(DEFAULT_FIXTURES["current"]["S02"]),
            alerts=deepcopy(DEFAULT_FIXTURES["alerts"]),
            forecast=_forecast(),
            profile={"user_id": "profile-user", "group": group},
        )


@pytest.mark.asyncio
async def test_outdoor_question_calls_required_tools_and_records_policy_version():
    graph = build_graph(FakeBackendToolClient())
    result = await graph.ainvoke(
        {
            "query": "Tôi có nên chạy bộ tại S02 trong 3 giờ tới không?",
            "user_id": "demo-user",
            "request_id": "req-recommendation",
        }
    )

    assert result["used_tools"] == [
        "get_current_pm25",
        "get_weather_context",
        "get_pm25_forecast",
        "get_active_alerts",
        "get_user_profile",
    ]
    assert "Quan sát tại S02" in result["answer"]
    assert "Dự báo (không phải quan sát hiện tại)" in result["answer"]
    assert "Khuyến nghị cho nhóm normal" in result["answer"]
    assert RECOMMENDATION_POLICY_VERSION in result["answer"]
    assert result["recommendation_policy_version"] == RECOMMENDATION_POLICY_VERSION
    assert result["trace"]["recommendation_policy_version"] == RECOMMENDATION_POLICY_VERSION
    assert {source["tool_name"] for source in result["sources"]} == {
        "get_current_pm25",
        "get_weather_context",
        "get_pm25_forecast",
        "get_active_alerts",
    }


@pytest.mark.asyncio
async def test_dashboard_station_context_is_used_without_parsing_station_from_message():
    graph = build_graph(FakeBackendToolClient())
    result = await graph.ainvoke(
        {
            "query": "Tôi có nên tập thể thao ngoài trời không?",
            "context_station_id": "S02",
            "user_id": "demo-user",
        }
    )

    assert result["route"]["tool_arguments"][0] == {"station_id": "S02"}
    assert "Quan sát tại S02" in result["answer"]


@pytest.mark.asyncio
async def test_missing_user_id_requests_clarification_without_profile_guess():
    graph = build_graph(FakeBackendToolClient())
    result = await graph.ainvoke({"query": "Tôi có nên chạy bộ tại S02 không?"})

    assert result["used_tools"] == []
    assert result["outcome"] == "clarification"
    assert "user_id" in result["answer"]


@pytest.mark.asyncio
async def test_stale_current_blocks_recommendation_and_environmental_sources():
    stale = deepcopy(DEFAULT_FIXTURES["current"]["S02"])
    stale.update({"is_stale": True, "status": "stale", "pm25": 999})
    adapter = FakeBackendToolClient({"current": {"S02": stale}})
    graph = build_graph(adapter)
    result = await graph.ainvoke(
        {
            "query": "Tôi có nên chạy bộ tại S02 không?",
            "user_id": "demo-user",
        }
    )

    assert result["answer"] == INSUFFICIENT_DATA_MESSAGE
    assert result["sources"] == []
    assert "999" not in result["answer"]
