from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal

ConversationIntent = Literal["domain", "greeting", "social", "clarification"]


@dataclass(frozen=True)
class ConversationDecision:
    intent: ConversationIntent
    kind: str
    fallback_response: str


class ConversationalAgentService:
    """Fail-closed conversation gate in front of the geospatial engine.

    Social messages never read telemetry. Unknown messages request clarification
    instead of falling through to an environmental recommendation. A separate
    Agent service may rewrite a social fallback, but this class validates that
    response before it reaches the public API.
    """

    _GREETINGS = {
        "e",
        "ee",
        "alo",
        "hi",
        "hello",
        "hey",
        "xin chao",
        "chao",
        "chao ban",
        "chao airguard",
        "xin chao airguard",
    }
    _THANKS_AND_ACKS = {
        "cam on",
        "cam on ban",
        "thanks",
        "thank you",
        "ok",
        "okay",
        "oke",
        "duoc",
        "duoc roi",
        "hieu roi",
        "ro roi",
        "hay qua",
        "tot lam",
    }
    _FAREWELLS = {"tam biet", "bye", "goodbye", "hen gap lai", "chao nhe"}
    _WELLBEING = {
        "khoe khong",
        "ban khoe khong",
        "hom nay ban the nao",
        "airguard khoe khong",
    }
    _CAPABILITIES = {
        "ban la ai",
        "airguard la gi",
        "ban lam duoc gi",
        "ban co the lam gi",
        "ban giup duoc gi",
        "chuc nang cua ban",
        "what can you do",
        "who are you",
    }
    _DOMAIN_SIGNALS = (
        "aqi",
        "pm2.5",
        "pm25",
        "co2",
        "chat luong khong khi",
        "moi truong",
        "o nhiem",
        "bui min",
        "tieng on",
        "nhiet do",
        "thoi tiet",
        "gio",
        "tram",
        "sensor",
        "canh bao",
        "du bao",
        "hien tai",
        "chay bo",
        "di bo",
        "tap the thao",
        "ngoai troi",
        "cung duong",
        "doan duong",
        "lo trinh",
        "tuyen duong",
        "so sanh",
        "khu vuc",
        "dia diem",
        "sapphire",
        "ho ngoc trai",
        "vinuni",
        "hai au",
        "san ho",
        "sao bien",
        "ocean park",
        "proposal",
        "phe duyet",
        "manager",
        "thong gio",
    )
    _CONTEXT_FOLLOW_UPS = (
        "o day",
        "cho nay",
        "khu nay",
        "the nao",
        "toi nay",
        "hom nay",
        "bay gio",
        "bao nhieu",
        "co tot",
        "co nen",
    )
    _UNSAFE_SOCIAL_PATTERNS = (
        r"\bS0[1-5]\b",
        r"\b\d+(?:[.,]\d+)?\s*(?:µg/m³|ug/m3|ppm|db|°c)\b",
        r"\bAQI\s+(?:la|là|dat|đạt|dang|đang)\b",
        r"\b(?:dang|đang)\s+(?:o nhiem|ô nhiễm)\b",
        r"\b(?:an toan|an toàn)\s+(?:de|để)\b",
    )

    @classmethod
    def classify(
        cls,
        message: str,
        *,
        station_id: str | None = None,
        map_context: dict[str, Any] | None = None,
    ) -> ConversationDecision:
        plain = cls._plain(message)
        if plain in cls._GREETINGS:
            return ConversationDecision(
                intent="greeting",
                kind="greeting",
                fallback_response=(
                    "Mình đây 👋 Bạn muốn kiểm tra chất lượng không khí, so sánh khu vực "
                    "hay tìm cung đường chạy bộ?"
                ),
            )
        if plain in cls._THANKS_AND_ACKS:
            return ConversationDecision(
                intent="social",
                kind="acknowledgement",
                fallback_response=(
                    "Rất vui được hỗ trợ bạn. Khi cần, bạn có thể hỏi AirGuard về AQI, "
                    "khu vực hoặc cung đường hoạt động ngoài trời."
                ),
            )
        if plain in cls._FAREWELLS:
            return ConversationDecision(
                intent="social",
                kind="farewell",
                fallback_response="Tạm biệt bạn! Hẹn gặp lại khi bạn cần hỗ trợ từ AirGuard.",
            )
        if plain in cls._WELLBEING:
            return ConversationDecision(
                intent="social",
                kind="wellbeing",
                fallback_response=(
                    "Mình đang hoạt động ổn và sẵn sàng hỗ trợ trong phạm vi AirGuard. "
                    "Bạn muốn xem chất lượng môi trường ở đâu?"
                ),
            )
        if plain in cls._CAPABILITIES:
            return ConversationDecision(
                intent="social",
                kind="capabilities",
                fallback_response=(
                    "Mình có thể hỗ trợ xem AQI và các chỉ số môi trường, so sánh khu vực, "
                    "xem dự báo ngắn hạn, cảnh báo và đề xuất cung đường chạy bộ dựa trên dữ liệu AirGuard."
                ),
            )

        if cls._is_domain_query(plain, station_id=station_id, map_context=map_context):
            return ConversationDecision(intent="domain", kind="domain", fallback_response="")

        return ConversationDecision(
            intent="clarification",
            kind="unclear",
            fallback_response=(
                "Mình chưa hiểu yêu cầu này. Bạn có thể hỏi về AQI hiện tại, so sánh khu vực, "
                "cảnh báo môi trường hoặc tìm cung đường chạy bộ."
            ),
        )

    @classmethod
    def deterministic_response(
        cls,
        decision: ConversationDecision,
        *,
        request_id: str,
        trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return cls._response(
            decision,
            answer=decision.fallback_response,
            request_id=request_id,
            trace=trace
            or {
                "intent": decision.intent,
                "conversation_kind": decision.kind,
                "generation_mode": "deterministic_grounded",
                "final_outcome": "clarification" if decision.intent == "clarification" else "direct_response",
            },
        )

    @classmethod
    def response_from_agent(
        cls,
        decision: ConversationDecision,
        agent_result: dict[str, Any],
        *,
        request_id: str,
    ) -> dict[str, Any]:
        answer = agent_result.get("answer")
        used_tools = agent_result.get("used_tools")
        sources = agent_result.get("sources")
        trace = agent_result.get("trace")
        agent_intent = trace.get("intent") if isinstance(trace, dict) else None
        if (
            not isinstance(answer, str)
            or not cls._social_text_is_safe(answer)
            or used_tools != []
            or sources != []
            or agent_intent not in {"greeting", "social"}
        ):
            return cls.deterministic_response(decision, request_id=request_id)
        safe_trace = dict(trace)
        safe_trace["conversation_kind"] = decision.kind
        return cls._response(decision, answer=answer.strip(), request_id=request_id, trace=safe_trace)

    @classmethod
    def _response(
        cls,
        decision: ConversationDecision,
        *,
        answer: str,
        request_id: str,
        trace: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "answer": {"summary": answer, "details": ""},
            "response": answer,
            "intent": decision.intent,
            "conversation_kind": decision.kind,
            "evidence": [],
            "sources": [],
            "map_actions": [],
            "used_tools": [],
            "request_id": request_id,
            "trace": trace,
        }

    @classmethod
    def _is_domain_query(
        cls,
        plain: str,
        *,
        station_id: str | None,
        map_context: dict[str, Any] | None,
    ) -> bool:
        if re.search(r"\bS0[1-5]\b", plain.upper()):
            return True
        if any(signal in plain for signal in cls._DOMAIN_SIGNALS):
            return True
        has_context = bool(station_id) or bool(
            map_context
            and any(map_context.get(key) for key in ("selected_sensor", "selected_location", "user_location"))
        )
        return has_context and any(signal in plain for signal in cls._CONTEXT_FOLLOW_UPS)

    @classmethod
    def _social_text_is_safe(cls, text: str) -> bool:
        cleaned = text.strip()
        if not cleaned or len(cleaned) > 500:
            return False
        return not any(re.search(pattern, cleaned, flags=re.IGNORECASE) for pattern in cls._UNSAFE_SOCIAL_PATTERNS)

    @staticmethod
    def _plain(value: str) -> str:
        normalized = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
        without_accents = "".join(
            character for character in normalized if unicodedata.category(character) != "Mn"
        )
        without_punctuation = re.sub(r"[^a-z0-9.\s]", " ", without_accents)
        return re.sub(r"\s+", " ", without_punctuation).strip()


conversational_agent = ConversationalAgentService()
