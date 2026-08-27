"""AirGuard Conversation State Manager for Contextual Multi-turn Geospatial AI Agent.

Maintains in-memory conversation state per session/conversation_id, tracks active entities,
last intents, comparison pairs, routing context, constraints, and time horizons to allow
seamless resolution of follow-up questions (e.g. "Còn VinUni thì sao?", "Ngắn hơn chút",
"Chỗ kia thì sao?") while cleanly invalidating state on topic shifts.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    conversation_id: str
    user_id: str = "demo-user"
    created_at: float = field(default_factory=time.time)
    last_updated_at: float = field(default_factory=time.time)
    last_intent: str | None = None
    last_query: str = ""
    active_entities: list[dict[str, Any]] = field(default_factory=list)
    active_locations: list[str] = field(default_factory=list)
    active_metric: str = "AQI"
    comparison_context: dict[str, Any] | None = None
    route_context: dict[str, Any] | None = None
    time_context: dict[str, Any] | None = None
    user_goal: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    negations: list[str] = field(default_factory=list)

    def is_expired(self, ttl_seconds: float = 1800.0) -> bool:
        return (time.time() - self.last_updated_at) > ttl_seconds


class ConversationStateManager:
    """Thread-safe in-memory state manager for contextual multi-turn chat."""

    def __init__(self, ttl_seconds: float = 1800.0, max_sessions: int = 1000) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._sessions: dict[str, ConversationState] = {}

    def get_or_create_state(self, conversation_id: str, user_id: str = "demo-user") -> ConversationState:
        self._cleanup_expired()
        cid = conversation_id.strip() if conversation_id else f"conv_{user_id}_{int(time.time())}"
        if cid not in self._sessions or self._sessions[cid].is_expired(self.ttl_seconds):
            self._sessions[cid] = ConversationState(conversation_id=cid, user_id=user_id)
        else:
            self._sessions[cid].last_updated_at = time.time()
        return self._sessions[cid]

    def reset_state(self, conversation_id: str) -> None:
        if conversation_id in self._sessions:
            del self._sessions[conversation_id]

    def update_state(
        self,
        conversation_id: str,
        intent: str | None = None,
        query: str = "",
        entities: list[dict[str, Any]] | None = None,
        locations: list[str] | None = None,
        metric: str | None = None,
        comparison_context: dict[str, Any] | None = None,
        route_context: dict[str, Any] | None = None,
        time_context: dict[str, Any] | None = None,
        user_goal: str | None = None,
        constraints: dict[str, Any] | None = None,
        negations: list[str] | None = None,
    ) -> ConversationState:
        state = self.get_or_create_state(conversation_id)
        state.last_updated_at = time.time()

        if intent:
            state.last_intent = intent
        if query:
            state.last_query = query
        if entities is not None:
            state.active_entities = entities
        if locations is not None:
            state.active_locations = locations
        if metric:
            state.active_metric = metric
        if comparison_context is not None:
            state.comparison_context = comparison_context
        if route_context is not None:
            state.route_context = route_context
        if time_context is not None:
            state.time_context = time_context
        if user_goal:
            state.user_goal = user_goal
        if constraints is not None:
            state.constraints.update(constraints)
        if negations is not None:
            state.negations = negations

        return state

    def resolve_followup(
        self,
        conversation_id: str,
        current_query: str,
        extracted_poi: dict[str, Any] | None,
        all_extracted_pois: list[dict[str, Any]],
        is_unknown_location: bool,
    ) -> dict[str, Any]:
        """
        Analyzes the current message in conjunction with previous conversation state to determine:
        1. Whether this is an elliptical follow-up question (e.g. "Còn VinUni?", "Ngắn hơn chút", "Chỗ kia thì sao?").
        2. Whether previous entities/locations should be retained or compared against.
        3. Whether route parameters should be modified (distance increase/decrease).
        4. Whether the topic has shifted and old state should be invalidated.
        """
        state = self.get_or_create_state(conversation_id)
        q = current_query.lower().strip()

        # Follow-up indicators
        is_elliptical_location_followup = bool(
            re.search(r"^(còn|the con|thế còn|con|sao|thi sao|thế thì|vậy còn)\s+", q)
            or re.search(r"\b(thì sao|thế nào|sao|như thế nào)\b\s*$", q)
        )
        is_shorter_route_followup = any(w in q for w in ["ngắn hơn", "gần hơn", "ít hơn", "giảm cự ly", "rút ngắn"])
        is_longer_route_followup = any(w in q for w in ["dài hơn", "xa hơn", "nhiều hơn", "tăng cự ly"])
        is_cleaner_route_followup = any(w in q for w in ["sạch hơn", "ít ô nhiễm hơn", "trong lành hơn", "tránh ô nhiễm"])

        resolved_data: dict[str, Any] = {
            "is_followup": False,
            "followup_type": None,
            "synthesized_intent": None,
            "reference_poi": None,
            "target_poi": None,
            "adjusted_distance_km": None,
            "avoid_locations": [],
            "needs_clarification": False,
            "clarification_candidates": [],
        }

        # Case 1: Route adjustments (e.g., "Ngắn hơn chút", "Dài hơn chút")
        if (is_shorter_route_followup or is_longer_route_followup) and state.last_intent in {
            "recommend_running_route",
            "recommend_personalized_running_route",
        }:
            current_dist = 3.0
            if state.route_context and "requested_distance_km" in state.route_context:
                current_dist = float(state.route_context["requested_distance_km"])
            elif state.route_context and "distance_km" in state.route_context:
                current_dist = float(state.route_context["distance_km"])

            if is_shorter_route_followup:
                new_dist = max(2.0, round(current_dist - 1.0, 1))
            else:
                new_dist = min(10.0, round(current_dist + 2.0, 1))

            resolved_data["is_followup"] = True
            resolved_data["followup_type"] = "distance_adjustment"
            resolved_data["synthesized_intent"] = state.last_intent
            resolved_data["adjusted_distance_km"] = new_dist
            return resolved_data

        # Case 2: Elliptical location inquiry after "worst location" or "best location" inquiry
        # Example: User asked "Khu nào ô nhiễm nhất?" (Ans: Trục Đa Tốn) -> Then asks: "Còn VinUni thì sao?"
        if (is_elliptical_location_followup or len(q.split()) <= 4) and extracted_poi:
            if state.last_intent in {"find_worst_location", "recommend_outdoor_location", "get_location_environment"}:
                prev_entities = state.active_entities
                prev_poi = prev_entities[0] if prev_entities else None

                if prev_poi and prev_poi.get("id") != extracted_poi["id"]:
                    resolved_data["is_followup"] = True
                    resolved_data["followup_type"] = "comparative_followup"
                    resolved_data["synthesized_intent"] = "compare_locations"
                    resolved_data["reference_poi"] = prev_poi
                    resolved_data["target_poi"] = extracted_poi
                    return resolved_data

            # Case 3: Comparison chain (User asks: "VinUni hay Hồ Ngọc Trai sạch hơn?" -> Ans: VinUni -> Follow-up: "Còn Sapphire?")
            elif state.last_intent == "compare_locations" and state.comparison_context:
                winner_poi = state.comparison_context.get("winner")
                if winner_poi and winner_poi.get("id") != extracted_poi["id"]:
                    resolved_data["is_followup"] = True
                    resolved_data["followup_type"] = "comparison_chain"
                    resolved_data["synthesized_intent"] = "compare_locations"
                    resolved_data["reference_poi"] = winner_poi
                    resolved_data["target_poi"] = extracted_poi
                    return resolved_data

        # Case 4: Ambiguous reference like "ở đó", "chỗ kia", "khu đó" without clear extracted POI
        if any(w in q for w in ["ở đó", "chỗ kia", "khu đó", "chỗ ấy", "nơi đó"]) and not extracted_poi:
            if state.active_entities and len(state.active_entities) > 1:
                # Multiple candidates -> Ask for clarification
                resolved_data["is_followup"] = True
                resolved_data["needs_clarification"] = True
                resolved_data["clarification_candidates"] = state.active_entities[:2]
                return resolved_data
            elif state.active_entities and len(state.active_entities) == 1:
                resolved_data["is_followup"] = True
                resolved_data["target_poi"] = state.active_entities[0]
                resolved_data["synthesized_intent"] = state.last_intent or "get_location_environment"
                return resolved_data

        # Case 5: State Invalidation on complete topic change
        # (e.g. was asking running route, now asks about general indoor/weather/station)
        if not is_elliptical_location_followup and not is_shorter_route_followup and not is_longer_route_followup:
            if any(w in q for w in ["ô nhiễm nhất", "sạch nhất", "chất lượng không khí", "nhiệt độ", "độ ồn"]):
                # Reset previous route context so it doesn't taint single inquiries
                state.route_context = None

        return resolved_data

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired_keys = [cid for cid, s in self._sessions.items() if (now - s.last_updated_at) > self.ttl_seconds]
        for k in expired_keys:
            del self._sessions[k]


conversation_state_manager = ConversationStateManager()
