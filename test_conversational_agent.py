from __future__ import annotations

import pytest

from backend.app.services.conversational_agent_service import ConversationalAgentService


@pytest.mark.parametrize(
    ("message", "intent", "kind"),
    [
        ("ê", "greeting", "greeting"),
        ("Alo!", "greeting", "greeting"),
        ("cảm ơn bạn", "social", "acknowledgement"),
        ("bạn khỏe không?", "social", "wellbeing"),
        ("bạn làm được gì?", "social", "capabilities"),
        ("tạm biệt", "social", "farewell"),
    ],
)
def test_basic_social_messages_are_classified_without_domain_fallthrough(message, intent, kind):
    decision = ConversationalAgentService.classify(
        message,
        station_id="S01",
        map_context={"selected_sensor": "S01"},
    )

    assert decision.intent == intent
    assert decision.kind == kind


def test_domain_message_with_social_prefix_still_routes_to_environmental_flow():
    decision = ConversationalAgentService.classify(
        "Xin chào, AQI tại VinUni hiện tại thế nào?",
        station_id="S04",
    )

    assert decision.intent == "domain"


def test_contextual_follow_up_remains_a_domain_query():
    decision = ConversationalAgentService.classify(
        "Tối nay thì sao?",
        map_context={"selected_location": "Hồ Ngọc Trai"},
    )

    assert decision.intent == "domain"


def test_sensitive_group_advice_reaches_the_grounded_agent():
    decision = ConversationalAgentService.classify(
        "Tôi thuộc nhóm nhạy cảm, nên làm gì?",
        station_id="S03",
    )

    assert decision.intent == "domain"


def test_running_distance_follow_up_is_a_domain_route_request():
    decision = ConversationalAgentService.classify("Tôi chỉ muốn chạy 2km thôi")

    assert decision.intent == "domain"


def test_unknown_message_requests_clarification_without_environmental_facts():
    decision = ConversationalAgentService.classify("ừm... abcxyz")
    response = ConversationalAgentService.deterministic_response(decision, request_id="req-clarify")

    assert decision.intent == "clarification"
    assert response["intent"] == "clarification"
    assert response["used_tools"] == []
    assert response["evidence"] == []
    assert response["map_actions"] == []
    assert "AQI hiện tại" in response["response"]


def test_agent_social_rewrite_is_accepted_only_without_tools_or_environmental_claims():
    decision = ConversationalAgentService.classify("ê")
    accepted = ConversationalAgentService.response_from_agent(
        decision,
        {
            "answer": "Mình đây 👋 Bạn muốn AirGuard hỗ trợ nội dung nào?",
            "used_tools": [],
            "sources": [],
            "trace": {"intent": "greeting", "generation_mode": "live_llm"},
        },
        request_id="req-social",
    )
    rejected = ConversationalAgentService.response_from_agent(
        decision,
        {
            "answer": "AQI tại S01 là 190 và đang ô nhiễm.",
            "used_tools": [],
            "sources": [],
            "trace": {"intent": "greeting", "generation_mode": "live_llm"},
        },
        request_id="req-social-unsafe",
    )

    assert accepted["response"] == "Mình đây 👋 Bạn muốn AirGuard hỗ trợ nội dung nào?"
    assert accepted["trace"]["generation_mode"] == "live_llm"
    assert rejected["response"] == decision.fallback_response
    assert rejected["trace"]["generation_mode"] == "deterministic_grounded"
