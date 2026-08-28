"""AirGuard Conversation State Manager for Contextual Multi-turn Geospatial AI Agent.

Maintains 4-layer in-memory conversation state per session/conversation_id:
1. Dialogue Context: tracks pending agent offers, pending actions, questions, and awaiting slots.
2. Task Context: tracks current user goal, activity, activity subtype (gym/walking/cycling), target distance, and constraints.
3. Spatial Context: tracks active location, focused POI/sensor, origin, destination, and route ID.
4. Environmental Context: tracks active metric (AQI/PM2.5) and time horizon (live/forecast).

Resolves short follow-up turns ("tìm cho tôi", "được", "3", "ngắn hơn chút", "còn ở đó?", "thôi")
before naive intent classification.
"""

from __future__ import annotations

import copy
import logging
import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    if not text:
        return ""
    s = text.lower().strip()
    s = s.replace("đ", "d").replace("Đ", "D")
    replacements = {
        "ư": "u", "Ư": "U", "ơ": "o", "Ơ": "O",
        "ê": "e", "Ê": "E", "ô": "o", "Ô": "O",
        "â": "a", "Â": "A", "ă": "a", "Ă": "A",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    nfkd = unicodedata.normalize("NFKD", s)
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    without_punct = re.sub(r"[^\w\s]", " ", without_accents)
    return re.sub(r"\s+", " ", without_punct).strip()


@dataclass
class ConversationState:
    conversation_id: str
    user_id: str = "demo-user"
    created_at: float = field(default_factory=time.time)
    last_updated_at: float = field(default_factory=time.time)
    turn_count: int = 0

    # Layer 1: Dialogue Context
    dialogue: dict[str, Any] = field(
        default_factory=lambda: {
            "current_topic": None,
            "last_agent_question": None,
            "last_agent_offer": None,
            "pending_action": None,
            "awaiting_user_input": None,
            "pending_action_ttl_turns": 3,
        }
    )

    # Layer 2: Task Context
    task: dict[str, Any] = field(
        default_factory=lambda: {
            "intent": None,
            "goal": None,
            "activity": None,
            "activity_subtype": None,
            "target_distance_km": None,
            "constraints": {},
        }
    )

    # Layer 3: Spatial Context
    spatial: dict[str, Any] = field(
        default_factory=lambda: {
            "active_location": None,
            "focused_poi_id": None,
            "focused_sensor_id": None,
            "previous_locations": [],
            "origin": None,
            "destination": None,
            "active_route_id": None,
        }
    )

    # Layer 4: Environmental Context
    environment: dict[str, Any] = field(
        default_factory=lambda: {
            "metric": "AQI",
            "time_context": None,
        }
    )

    # Backward-compatible convenience fields
    active_domain: str = "airguard"
    domain_context: dict[str, Any] = field(default_factory=dict)
    current_turn_intent: str | None = None
    last_intent: str | None = None
    last_query: str = ""
    active_scope: str = "ocp1"
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

    CORRECTION_PATTERNS = [
        r"^(?:ý\s+là|y\s+la)\b",
        r"^(?:ý\s+tôi\s+là|y\s+toi\s+la)\b",
        r"^(?:ý\s+mình\s+là|y\s+minh\s+la)\b",
        r"^(?:ý\s+em\s+là|y\s+em\s+la)\b",
        r"^(?:không\s*,?\s*tôi\s+hỏi|khong\s*,?\s*toi\s+hoi)\b",
        r"^(?:không\s+phải|khong\s+phai)\b",
        r"^(?:tôi\s+hỏi\s+chung|toi\s+hoi\s+chung)\b",
        r"^(?:ý\s+tôi\s+hỏi\s+toàn\s+khu|y\s+toi\s+hoi\s+toan\s+khu)\b",
        r"^(?:tôi\s+muốn\s+nói|toi\s+muon\s+noi)\b",
        r"^(?:không\s*,?\s*ý\s+là|khong\s*,?\s*y\s+la)\b",
        r"^(?:không\s*,?\s*|khong\s*,?\s*)(?=\d+\s*(?:km|kilo|cay))",
    ]

    ACCEPT_PHRASES = {
        "tim cho toi", "tim di", "lam di", "duoc", "duoc chu", "duoc do", "duoc nhe",
        "ok", "oke", "okay", "u", "um", "uh", "uhm", "co", "thu xem", "thu di",
        "dong y", "yes", "yeah", "yep", "chuan", "dung roi", "chay luon",
        "tim giup toi", "tim giup", "lam giup toi", "trien khai di", "xem giup toi",
        "tim ho toi", "tim luon", "dung", "chinh xac", "dung the",
    }

    REJECT_PHRASES = {
        "thoi", "khong", "khoi", "khong can", "bo di", "cancel", "huy",
        "dung lai", "khong muon", "thoi khoi", "khoi can", "khong nhe", "thoi nhe",
    }

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

    def set_pending_action(
        self,
        conversation_id: str,
        action_type: str,
        known_slots: dict[str, Any] | None = None,
        required_slots: list[str] | None = None,
        ttl_turns: int = 3,
    ) -> None:
        state = self.get_or_create_state(conversation_id)
        state.dialogue["pending_action"] = {
            "type": action_type,
            "status": "awaiting_confirmation",
            "known_slots": known_slots or {},
            "required_slots": required_slots or [],
            "created_turn": state.turn_count,
            "ttl_turns": ttl_turns,
        }
        state.dialogue["last_agent_offer"] = {
            "action": action_type,
            "parameters": known_slots or {},
            "status": "awaiting_confirmation",
        }
        state.last_updated_at = time.time()

    def clear_pending_action(self, conversation_id: str) -> None:
        state = self.get_or_create_state(conversation_id)
        state.dialogue["pending_action"] = None
        state.dialogue["last_agent_offer"] = None
        state.last_updated_at = time.time()

    def set_awaiting_slot(
        self,
        conversation_id: str,
        slot_name: str,
        for_intent: str = "",
        options: list[Any] | None = None,
    ) -> None:
        state = self.get_or_create_state(conversation_id)
        state.dialogue["awaiting_user_input"] = {
            "type": "slot",
            "slot": slot_name,
            "for_intent": for_intent,
            "options": options or [],
            "created_turn": state.turn_count,
        }
        state.dialogue["last_agent_question"] = {
            "slot": slot_name,
            "for_intent": for_intent,
            "options": options or [],
        }
        state.last_updated_at = time.time()

    def clear_awaiting_slot(self, conversation_id: str) -> None:
        state = self.get_or_create_state(conversation_id)
        state.dialogue["awaiting_user_input"] = None
        state.last_updated_at = time.time()

    def detect_correction(self, message: str) -> tuple[bool, str]:
        if not message:
            return False, ""
        msg_clean = message.strip()
        for pat in self.CORRECTION_PATTERNS:
            match = re.search(pat, msg_clean, flags=re.IGNORECASE)
            if match:
                corrected = msg_clean[match.end():].lstrip(",.:; \t\n")
                if not corrected:
                    corrected = msg_clean
                return True, corrected
        return False, msg_clean

    def invalidate_conflicting_context(self, conversation_id: str, new_scope: str = "ocp1") -> ConversationState:
        state = self.get_or_create_state(conversation_id)
        state.active_entities = []
        state.active_locations = []
        state.comparison_context = None
        state.route_context = None
        state.active_scope = new_scope
        state.spatial["active_location"] = None
        state.spatial["focused_poi_id"] = None
        state.spatial["previous_locations"] = []
        state.last_updated_at = time.time()
        return state

    def update_state(
        self,
        conversation_id: str,
        intent: str | None = None,
        query: str = "",
        scope: str | None = None,
        entities: list[dict[str, Any]] | None = None,
        locations: list[str] | None = None,
        metric: str | None = None,
        comparison_context: dict[str, Any] | None = None,
        route_context: dict[str, Any] | None = None,
        time_context: dict[str, Any] | None = None,
        user_goal: str | None = None,
        constraints: dict[str, Any] | None = None,
        negations: list[str] | None = None,
        activity_type: str | None = None,
        activity_subtype: str | None = None,
        target_distance_km: float | None = None,
    ) -> ConversationState:
        state = self.get_or_create_state(conversation_id)
        state.last_updated_at = time.time()
        state.turn_count += 1

        is_social = intent and (
            intent.startswith("social.")
            or intent in {"greeting", "social", "clarification", "out_of_scope"}
        )

        if is_social:
            state.active_domain = "social"
            state.current_turn_intent = intent
            if query:
                state.last_query = query
            return state

        state.active_domain = "airguard"
        if intent:
            state.last_intent = intent
            state.current_turn_intent = intent
            state.task["intent"] = intent
        if query:
            state.last_query = query
        if scope:
            state.active_scope = scope
        if entities is not None:
            state.active_entities = entities
            if entities:
                state.spatial["focused_poi_id"] = entities[0].get("id")
                state.spatial["focused_sensor_id"] = entities[0].get("sensor_id")
        if locations is not None:
            state.active_locations = locations
            if locations:
                state.spatial["active_location"] = locations[0]
                state.spatial["previous_locations"].extend(locations[1:])
        if metric:
            state.active_metric = metric
            state.environment["metric"] = metric
        if comparison_context is not None:
            state.comparison_context = comparison_context
        if route_context is not None:
            state.route_context = route_context
            state.spatial["active_route_id"] = route_context.get("route_id")
        if time_context is not None:
            state.time_context = time_context
            state.environment["time_context"] = time_context
        if user_goal:
            state.user_goal = user_goal
            state.task["goal"] = user_goal
        if activity_type:
            state.task["activity"] = activity_type
        if activity_subtype:
            state.task["activity_subtype"] = activity_subtype
        if target_distance_km is not None:
            state.task["target_distance_km"] = target_distance_km
        if constraints is not None:
            state.constraints.update(constraints)
            state.task["constraints"].update(constraints)
        if negations is not None:
            state.negations = negations

        state.domain_context = {
            "last_intent": state.last_intent,
            "entities": list(state.active_entities),
            "locations": list(state.active_locations),
            "scope": state.active_scope,
            "task": dict(state.task),
            "spatial": dict(state.spatial),
        }

        return state

    def resolve_conversation_turn(
        self,
        conversation_id: str,
        message: str,
        map_context: dict[str, Any] | None = None,
        peek: bool = False,
    ) -> dict[str, Any]:
        """
        Deep Context & Follow-up Resolver.
        Evaluates dialogue state, pending actions, awaiting slots, modifications,
        and anaphoric references before naive intent classification.
        """
        state = self.get_or_create_state(conversation_id)
        map_context = map_context or {}
        q = message.strip()
        q_norm = _normalize(q)

        default_result: dict[str, Any] = {
            "resolution_type": "none",
            "resolved_intent": None,
            "pending_action": None,
            "slot_name": None,
            "slot_value": None,
            "modified_params": None,
            "target_poi": None,
            "needs_clarification": False,
            "clarification_candidates": [],
            "cleaned_message": q,
        }

        if not q:
            return default_result

        # -------------------------------------------------------------
        # 1. Conversational Correction
        # -------------------------------------------------------------
        is_correction, cleaned_msg = self.detect_correction(q)
        if is_correction:
            cleaned_norm = _normalize(cleaned_msg)
            # Check if correction specifies distance
            dist_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:km|kilo|cay)?\b", cleaned_norm)
            if dist_match and state.last_intent in {"recommend_running_route", "recommend_personalized_running_route"}:
                dist_val = float(dist_match.group(1))
                return {
                    "resolution_type": "modify",
                    "resolved_intent": state.last_intent,
                    "modified_params": {"distance_km": dist_val},
                    "cleaned_message": cleaned_msg,
                }
            return {
                "resolution_type": "correction",
                "resolved_intent": None,
                "cleaned_message": cleaned_msg,
            }

        # -------------------------------------------------------------
        # 2. Reject Pending Action
        # -------------------------------------------------------------
        if q_norm in self.REJECT_PHRASES or any(q_norm.startswith(r + " ") for r in self.REJECT_PHRASES):
            if state.dialogue.get("pending_action"):
                if not peek:
                    self.clear_pending_action(conversation_id)
                    self.clear_awaiting_slot(conversation_id)
                return {
                    "resolution_type": "reject_pending_action",
                    "resolved_intent": "conversation.reject",
                }

        # -------------------------------------------------------------
        # 3. Accept Pending Action (e.g. "tìm cho tôi", "được", "ok", "làm đi")
        # -------------------------------------------------------------
        is_accept = (
            q_norm in self.ACCEPT_PHRASES
            or any(q_norm.startswith(a + " ") for a in self.ACCEPT_PHRASES)
            or q_norm in {"tim", "lam", "chay", "di", "ok luon", "duoc luon"}
        )

        if is_accept and state.dialogue.get("pending_action"):
            pending = state.dialogue["pending_action"]
            # Check TTL
            created_turn = pending.get("created_turn", 0)
            ttl = pending.get("ttl_turns", 3)
            if (state.turn_count - created_turn) <= ttl:
                return {
                    "resolution_type": "accept_pending_action",
                    "resolved_intent": pending.get("type"),
                    "pending_action": pending,
                    "known_slots": pending.get("known_slots", {}),
                    "required_slots": pending.get("required_slots", []),
                }
            else:
                if not peek:
                    self.clear_pending_action(conversation_id)

        # -------------------------------------------------------------
        # 4. Awaiting Slot Filling
        # -------------------------------------------------------------
        if state.dialogue.get("awaiting_user_input"):
            awaiting = state.dialogue["awaiting_user_input"]
            slot_name = awaiting.get("slot")
            for_intent = awaiting.get("for_intent")
            options = awaiting.get("options", [])

            # Slot A: distance_km
            if slot_name == "distance_km":
                # Check direct number
                num_match = re.search(r"\b(\d+(?:\.\d+)?)\b", q_norm)
                if num_match:
                    val = float(num_match.group(1))
                    if not peek:
                        self.clear_awaiting_slot(conversation_id)
                    return {
                        "resolution_type": "answer_slot",
                        "slot_name": "distance_km",
                        "slot_value": val,
                        "for_intent": for_intent,
                    }
                # Check ordinal references: "cái giữa", "cái đầu", "cái cuối", "lựa chọn 2"
                if options:
                    if any(w in q_norm for w in ["cai dau", "phuong an 1", "lua chon 1", "so 1", "dau tien"]):
                        val = float(options[0])
                        if not peek:
                            self.clear_awaiting_slot(conversation_id)
                        return {"resolution_type": "answer_slot", "slot_name": "distance_km", "slot_value": val, "for_intent": for_intent}
                    elif any(w in q_norm for w in ["cai giua", "phuong an 2", "lua chon 2", "so 2", "o giua", "muc giua"]):
                        val = float(options[1] if len(options) > 1 else options[0])
                        if not peek:
                            self.clear_awaiting_slot(conversation_id)
                        return {"resolution_type": "answer_slot", "slot_name": "distance_km", "slot_value": val, "for_intent": for_intent}
                    elif any(w in q_norm for w in ["cai cuoi", "phuong an 3", "lua chon 3", "so 3", "cuoi cung"]):
                        val = float(options[-1])
                        if not peek:
                            self.clear_awaiting_slot(conversation_id)
                        return {"resolution_type": "answer_slot", "slot_name": "distance_km", "slot_value": val, "for_intent": for_intent}

            # Slot B: indoor_outdoor_choice
            elif slot_name == "indoor_outdoor_choice":
                if any(w in q_norm for w in ["trong nha", "indoor", "nha"]):
                    if not peek:
                        self.clear_awaiting_slot(conversation_id)
                    return {
                        "resolution_type": "answer_slot",
                        "slot_name": "indoor_outdoor_choice",
                        "slot_value": "indoor",
                        "for_intent": "find_nearby_indoor_places",
                    }
                elif any(w in q_norm for w in ["ngoai troi", "outdoor", "ngoai", "chay ngoai"]):
                    if not peek:
                        self.clear_awaiting_slot(conversation_id)
                    return {
                        "resolution_type": "answer_slot",
                        "slot_name": "indoor_outdoor_choice",
                        "slot_value": "outdoor",
                        "for_intent": "recommend_running_route",
                    }

            # Slot C: activity_subtype (e.g. gym, đi bộ trong nhà)
            elif slot_name == "activity_subtype":
                if any(w in q_norm for w in ["gym", "phong tap", "fitness", "yoga", "chay may"]):
                    if not peek:
                        self.clear_awaiting_slot(conversation_id)
                    return {
                        "resolution_type": "answer_slot",
                        "slot_name": "activity_subtype",
                        "slot_value": "gym",
                        "for_intent": for_intent or "find_nearby_indoor_places",
                    }
                elif any(w in q_norm for w in ["di bo", "shopping", "mua sam", "tttm", "vincom", "thu gian"]):
                    if not peek:
                        self.clear_awaiting_slot(conversation_id)
                    return {
                        "resolution_type": "answer_slot",
                        "slot_name": "activity_subtype",
                        "slot_value": "walking",
                        "for_intent": for_intent or "find_nearby_indoor_places",
                    }

            # Slot D: origin
            elif slot_name == "origin":
                try:
                    from .spatial_registry import spatial_registry
                    matched_poi = spatial_registry.find_poi_by_name(q)
                    if matched_poi:
                        if not peek:
                            self.clear_awaiting_slot(conversation_id)
                        return {
                            "resolution_type": "answer_slot",
                            "slot_name": "origin",
                            "slot_value": matched_poi["short_name"],
                            "for_intent": for_intent,
                        }
                except Exception:
                    pass

        # -------------------------------------------------------------
        # 5. Task Modifications (Distance & Avoidance Constraints)
        # -------------------------------------------------------------
        if state.last_intent in {"recommend_running_route", "recommend_personalized_running_route"}:
            # Shorter / longer
            is_shorter = any(w in q_norm for w in ["ngan hon", "ngan hon chut", "it hon", "rut ngan", "giam cu ly"])
            is_longer = any(w in q_norm for w in ["dai hon", "dai hon chut", "xa hon", "nhieu hon", "tang cu ly"])
            num_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:km|cay|kilo)?\s*(?:thoi|nhe|thoi nhe|thoi a)?\b", q_norm)

            if is_shorter or is_longer or (num_match and len(q_norm.split()) <= 4):
                current_dist = state.task.get("target_distance_km") or 3.0
                if num_match:
                    new_dist = float(num_match.group(1))
                elif is_shorter:
                    new_dist = max(2.0, round(current_dist - 1.0, 1))
                else:
                    new_dist = min(10.0, round(current_dist + 2.0, 1))

                return {
                    "resolution_type": "modify",
                    "resolved_intent": state.last_intent,
                    "modified_params": {"distance_km": new_dist},
                }

            # Avoidance constraints: "nhưng tránh Đa Tốn nhé", "tránh Đa Tốn"
            avoid_match = re.search(r"\b(?:tranh|khong qua|ne|khong di qua)\s+([a-zA-Z0-9\s_]+?)(?:nhe|nha|thoi|$)", q, flags=re.IGNORECASE)
            if avoid_match:
                avoid_target = avoid_match.group(1).strip()
                return {
                    "resolution_type": "modify",
                    "resolved_intent": "recommend_avoidance_running_route",
                    "modified_params": {"avoid_location": avoid_target},
                }

        # -------------------------------------------------------------
        # 6. Anaphora / Reference Resolution ("ở đó", "chỗ đó", "tới đó")
        # -------------------------------------------------------------
        is_anaphora = any(w in q_norm for w in ["o do", "cho do", "khu do", "toi do", "den do", "qua do", "noi do", "cho ay", "noi ay"])
        if is_anaphora:
            if state.active_entities and len(state.active_entities) > 1:
                # Ambiguous: 2 candidates from recent comparison
                return {
                    "resolution_type": "reference",
                    "needs_clarification": True,
                    "clarification_candidates": state.active_entities[:2],
                }
            elif state.active_entities and len(state.active_entities) == 1:
                target = state.active_entities[0]
                is_walking_inquiry = any(w in q_norm for w in ["di bo", "di bo toi", "mat bao lau", "bao xa", "khoang cach"])
                return {
                    "resolution_type": "reference",
                    "target_poi": target,
                    "resolved_intent": "get_walking_route_to_poi" if is_walking_inquiry else (state.last_intent or "get_location_environment"),
                }

        return default_result

    def resolve_followup(
        self,
        conversation_id: str,
        current_query: str,
        extracted_poi: dict[str, Any] | None,
        all_extracted_pois: list[dict[str, Any]],
        is_unknown_location: bool,
    ) -> dict[str, Any]:
        """Backward-compatible wrapper around follow-up resolution."""
        turn_res = self.resolve_conversation_turn(conversation_id, current_query)
        if turn_res["resolution_type"] in {"modify", "accept_pending_action", "reference"}:
            return {
                "is_followup": True,
                "followup_type": turn_res["resolution_type"],
                "synthesized_intent": turn_res.get("resolved_intent"),
                "reference_poi": None,
                "target_poi": turn_res.get("target_poi"),
                "adjusted_distance_km": (turn_res.get("modified_params") or {}).get("distance_km"),
                "avoid_locations": [(turn_res.get("modified_params") or {}).get("avoid_location")] if (turn_res.get("modified_params") or {}).get("avoid_location") else [],
                "needs_clarification": turn_res.get("needs_clarification", False),
                "clarification_candidates": turn_res.get("clarification_candidates", []),
            }

        state = self.get_or_create_state(conversation_id)
        q = current_query.lower().strip()
        q_norm = _normalize(q)

        is_elliptical = bool(
            re.search(r"^(còn|the con|thế còn|con|sao|thi sao|thế thì|vậy còn)\s+", q)
            or re.search(r"\b(thì sao|thế nào|sao|như thế nào)\b\s*$", q)
        )

        if (is_elliptical or len(q.split()) <= 4) and extracted_poi:
            if state.last_intent in {"find_worst_location", "recommend_outdoor_location", "get_location_environment"}:
                prev_entities = state.active_entities
                prev_poi = prev_entities[0] if prev_entities else None
                if prev_poi and prev_poi.get("id") != extracted_poi["id"]:
                    return {
                        "is_followup": True,
                        "followup_type": "comparative_followup",
                        "synthesized_intent": "compare_locations",
                        "reference_poi": prev_poi,
                        "target_poi": extracted_poi,
                        "adjusted_distance_km": None,
                        "avoid_locations": [],
                        "needs_clarification": False,
                        "clarification_candidates": [],
                    }
            elif state.last_intent == "compare_locations" and state.comparison_context:
                winner_poi = state.comparison_context.get("winner")
                if winner_poi and winner_poi.get("id") != extracted_poi["id"]:
                    return {
                        "is_followup": True,
                        "followup_type": "comparison_chain",
                        "synthesized_intent": "compare_locations",
                        "reference_poi": winner_poi,
                        "target_poi": extracted_poi,
                        "adjusted_distance_km": None,
                        "avoid_locations": [],
                        "needs_clarification": False,
                        "clarification_candidates": [],
                    }

        return {
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

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired_keys = [cid for cid, s in self._sessions.items() if (now - s.last_updated_at) > self.ttl_seconds]
        for k in expired_keys:
            del self._sessions[k]


conversation_state_manager = ConversationStateManager()
