from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.agents.policies.grounding import Intent, route_query
from src.models.schemas import ChatRequest


def _context(*station_ids: str, last_intent: str = "current") -> dict:
    return {
        "context_version": 1,
        "station_ids": list(station_ids),
        "primary_station_id": station_ids[0] if station_ids else None,
        "last_intent": last_intent,
        "turn_count": 1,
    }


def test_follow_up_forecast_uses_memory_before_static_ui_station() -> None:
    decision = route_query(
        "Còn 3 giờ tới thì sao?",
        context_station_id="S01",
        user_id="demo-user",
        conversation_context=_context("S03"),
    )

    assert decision.intent == Intent.FORECAST
    assert decision.tool_arguments == [{"station_id": "S03", "hours": 3, "metric": "pm25"}]


def test_follow_up_comparison_combines_antecedent_with_explicit_station() -> None:
    decision = route_query(
        "So với S04 thì sao?",
        context_station_id="S01",
        conversation_context=_context("S03"),
    )

    assert decision.intent == Intent.COMPARE
    assert decision.tool_arguments == [{"station_ids": ["S03", "S04"]}]


def test_follow_up_comparison_reuses_previous_validated_pair() -> None:
    decision = route_query(
        "Trạm nào tốt hơn?",
        conversation_context=_context("S02", "S03", last_intent="compare"),
    )

    assert decision.intent == Intent.COMPARE
    assert decision.tool_arguments == [{"station_ids": ["S02", "S03"]}]


def test_follow_up_without_memory_still_clarifies_instead_of_guessing() -> None:
    decision = route_query("Còn 3 giờ tới thì sao?")

    assert decision.intent == Intent.CLARIFICATION
    assert decision.tool_calls == []


def test_agent_request_rejects_environmental_values_in_memory_contract() -> None:
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(
            {
                "message": "Còn 3 giờ tới thì sao?",
                "user_id": "demo-user",
                "conversation_context": {
                    "context_version": 1,
                    "station_ids": ["S03"],
                    "aqi": 99,
                },
            }
        )


def test_agent_request_rejects_non_allowlisted_memory_station() -> None:
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(
            {
                "message": "Còn trạm đó?",
                "conversation_context": {
                    "context_version": 1,
                    "station_ids": ["S99"],
                },
            }
        )


def test_agent_request_rejects_inconsistent_or_untrusted_memory_metadata() -> None:
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(
            {
                "message": "Còn trạm đó?",
                "conversation_context": {
                    "context_version": 1,
                    "station_ids": ["S03"],
                    "primary_station_id": "S04",
                    "last_intent": "ignore_previous_policy",
                },
            }
        )
