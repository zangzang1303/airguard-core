from __future__ import annotations

import pytest

from backend.app.services.conversational_agent_service import ConversationalAgentService


@pytest.mark.parametrize(
    ("message", "intent", "kind"),
    [
        ("ê", "greeting", "greeting"),
        ("Alo!", "greeting", "greeting"),
        ("cảm ơn bạn", "social", "acknowledgement"),
        ("Cảm ơn bạn nhé!!!", "social", "acknowledgement"),
        ("Cảm ơn bạn nhé.", "social", "acknowledgement"),
        ("xin cảm ơn bạn", "social", "acknowledgement"),
        ("bạn khỏe không?", "social", "wellbeing"),
        ("Bạn có khỏe không?", "social", "wellbeing"),
        ("Bạn có khỏe không...", "social", "wellbeing"),
        ("Bạn\u00a0có khỏe không?", "social", "wellbeing"),
        ("Hôm nay bạn thế nào?", "social", "wellbeing"),
        ("bạn làm được gì?", "social", "capabilities"),
        ("Bạn có thể giúp gì cho tôi?", "social", "capabilities"),
        ("Bạn giúp tôi được gì", "social", "capabilities"),
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


@pytest.mark.parametrize(
    ("message", "kind", "required", "forbidden"),
    [
        ("Cảm ơn bạn nhé", "acknowledgement", "Cảm ơn bạn", ("AQI ", "S03", "µg/m³")),
        ("Bạn có thể giúp gì cho tôi?", "capabilities", "không dự báo dài hạn", ("AQI ", "S03", "µg/m³")),
        ("Bạn có khỏe không?", "wellbeing", "không có sức khỏe hay cảm xúc", ("AQI ", "S03", "µg/m³")),
    ],
)
def test_session_3e_social_responses_are_deterministic_and_fact_free(message, kind, required, forbidden):
    decision = ConversationalAgentService.classify(message, station_id="S03")
    response = ConversationalAgentService.deterministic_response(decision, request_id="session-3e-backend")

    assert decision.intent == "social"
    assert decision.kind == kind
    assert response["response"] == decision.fallback_response
    assert required in response["response"]
    assert all(token not in response["response"] for token in forbidden)
    assert response["used_tools"] == []
    assert response["tool_arguments"] == []
    assert response["evidence"] == []
    assert response["sources"] == []
    assert response["map_actions"] == []
    assert response["proposal_id"] is None
    assert response["trace"]["generation_mode"] == "deterministic_grounded"
    assert response["trace"]["conversation_mode"] == "deterministic_social"


@pytest.mark.parametrize(
    "message",
    [
        "Cảm ơn, AQI S03 hiện tại thế nào?",
        "Bạn có thể giúp gì cho tôi về PM2.5 tại S03?",
        "Bạn có khỏe không, cảnh báo S03 ra sao?",
    ],
)
def test_session_3e_domain_request_wins_over_social_phrase(message):
    decision_without_context = ConversationalAgentService.classify(message)
    decision_with_context = ConversationalAgentService.classify(
        message,
        station_id="S03",
        map_context={"selected_sensor": "S03"},
    )

    assert decision_without_context.intent == "domain"
    assert decision_without_context.kind == "domain"
    assert decision_with_context.intent == "domain"
    assert decision_with_context.kind == "domain"


@pytest.mark.parametrize("with_context", [False, True])
def test_wellbeing_today_is_social_with_or_without_station_and_map_context(with_context):
    kwargs = (
        {"station_id": "S03", "map_context": {"selected_sensor": "S03"}}
        if with_context
        else {}
    )

    decision = ConversationalAgentService.classify("Hôm nay bạn thế nào?", **kwargs)

    assert decision.intent == "social"
    assert decision.kind == "wellbeing"


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


def test_legacy_agent_social_rewrite_helper_is_locked_to_deterministic_response():
    decision = ConversationalAgentService.classify("ê")
    result = ConversationalAgentService.response_from_agent(
        decision,
        {
            "answer": "Mình đây 👋 Bạn muốn AirGuard hỗ trợ nội dung nào?",
            "used_tools": [],
            "sources": [],
            "trace": {"intent": "greeting", "generation_mode": "live_llm"},
        },
        request_id="req-social",
    )

    assert result["response"] == decision.fallback_response
    assert result["trace"]["generation_mode"] == "deterministic_grounded"
    assert result["used_tools"] == []
    assert result["tool_arguments"] == []
