from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal

ConversationIntent = Literal["domain", "greeting", "social", "clarification", "out_of_scope"]


@dataclass(frozen=True)
class ConversationDecision:
    intent: ConversationIntent
    kind: str
    fallback_response: str


class ConversationalAgentService:
    """Fail-closed conversation gate in front of the geospatial engine.

    Social messages never read telemetry or invoke the Agent/LLM. Unknown messages
    request clarification instead of falling through to an environmental
    recommendation.
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
        "chao airguard ai",
        "xin chao airguard ai",
        "hello airguard",
        "hello airguard ai",
    }
    _THANKS_AND_ACKS = {
        "cam on",
        "cam on ban",
        "cam on nhe",
        "cam on ban nhe",
        "xin cam on",
        "xin cam on ban",
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
        "ban co khoe khong",
        "hom nay ban the nao",
        "airguard khoe khong",
        "airguard co khoe khong",
    }
    _CAPABILITIES = {
        "ban la ai",
        "airguard la gi",
        "ban lam duoc gi",
        "ban lam duoc nhung gi",
        "ban co the lam gi",
        "ban co the lam duoc gi",
        "ban co the lam duoc nhung gi",
        "ban co the giup gi cho toi",
        "ban giup toi duoc gi",
        "ban co the ho tro gi",
        "ban giup duoc gi",
        "ban giup gi",
        "lam duoc gi",
        "giup duoc gi",
        "chuc nang cua ban",
        "what can you do",
        "who are you",
    }
    _DOMAIN_SIGNALS = (
        "aqi",
        "pm2.5",
        "pm25",
        "co2",
        "khong khi",
        "chat luong khong khi",
        "moi truong",
        "o nhiem",
        "bui min",
        "tieng on",
        "nhiet do",
        "thoi tiet",
        "mua",
        "bao",
        "do am",
        "nang",
        "gio",
        "tram",
        "sensor",
        "canh bao",
        "du bao",
        "hien tai",
        "toi nay",
        "chieu nay",
        "sang nay",
        "cho nay",
        "o day",
        "khu nay",
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
        "ngoc trai",
        "vinuni",
        "hai au",
        "san ho",
        "sao bien",
        "an dao",
        "dao ngoc trai",
        "zenpark",
        "ruby",
        "zurich",
        "pavilion",
        "vincom",
        "vinschool",
        "vinmec",
        "da ton",
        "bien ho",
        "ocean park",
        "ocean park 1",
        "proposal",
        "phe duyet",
        "manager",
        "thong gio",
        "chat luong",
        "ngan hon",
        "dai hon",
        "sach hon",
        "tranh",
        "con ",
        # A person can ask for cautious advice by naming their group without
        # repeating an AQI/running keyword.  This only admits the request to
        # the Agent; the Agent still obtains the authoritative group from the
        # backend profile in the same request.
        "nhom nhay cam",
        "nhay cam",
        "sensitive group",
        "nen lam gi",
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
    _DISTANCE_TARGET_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:km|cay|kilo(?:met)?)\b")
    _RUNNING_DISTANCE_CUES = (
        "chay",
        "di bo",
        "tap",
        "lo trinh",
        "cung duong",
        "tuyen duong",
        "doan duong",
    )
    _OUT_OF_SCOPE_SIGNALS = (
        "thuoc",
        "uong thuoc",
        "kham benh",
        "bac si",
        "chua benh",
        "dau dau",
        "sot",
        "gia nha",
        "gia can ho",
        "mua chung cu",
        "thue nha",
        "bat dong san",
        "quan an",
        "an gi ngon",
        "quan pho",
        "quan nhau",
        "nha hang",
        "quan cafe",
        "tac duong",
        "ket xe",
        "un tac",
        "viet code",
        "python",
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
        social_plain = cls._social_plain(message)
        # A concrete environmental request always wins over a social prefix.
        # Do this before exact social matching so, for example, "Cảm ơn, AQI
        # S03 hiện tại thế nào?" cannot be swallowed by an acknowledgement.
        if cls._has_explicit_domain_request(plain):
            return ConversationDecision(intent="domain", kind="domain", fallback_response="")
        if social_plain in cls._GREETINGS:
            return ConversationDecision(
                intent="greeting",
                kind="greeting",
                fallback_response=(
                    "Mình đây 👋 Bạn muốn kiểm tra chất lượng không khí, so sánh khu vực "
                    "hay tìm cung đường chạy bộ?"
                ),
            )
        if social_plain in cls._THANKS_AND_ACKS:
            return ConversationDecision(
                intent="social",
                kind="acknowledgement",
                fallback_response="Cảm ơn bạn. Rất vui được hỗ trợ trong phạm vi AirGuard.",
            )
        if social_plain in cls._FAREWELLS:
            return ConversationDecision(
                intent="social",
                kind="farewell",
                fallback_response="Tạm biệt bạn! Hẹn gặp lại khi bạn cần hỗ trợ từ AirGuard.",
            )
        if social_plain in cls._WELLBEING:
            return ConversationDecision(
                intent="social",
                kind="wellbeing",
                fallback_response=(
                    "Mình là trợ lý AI nên không có sức khỏe hay cảm xúc, nhưng có thể hỗ trợ về AirGuard."
                ),
            )
        if social_plain in cls._CAPABILITIES:
            return ConversationDecision(
                intent="social",
                kind="capabilities",
                fallback_response=(
                    "Mình hỗ trợ AQI/trạm hiện tại, so sánh trạm, dự báo baseline 1–3 giờ, cảnh báo và "
                    "khuyến nghị grounded từ dữ liệu demo/mô phỏng. Mình không dự báo dài hạn, chẩn đoán "
                    "hay điều khiển thiết bị."
                ),
            )

        if any(s in plain for s in cls._OUT_OF_SCOPE_SIGNALS):
            return ConversationDecision(
                intent="out_of_scope",
                kind="out_of_scope",
                fallback_response=(
                    "Yêu cầu này nằm ngoài phạm vi quan trắc của hệ thống AirGuard AI. "
                    "AirGuard là hệ thống chuyên về giám sát chất lượng không khí (AQI, PM2.5, CO₂), "
                    "cảnh báo môi trường và gợi ý lộ trình vận động ngoài trời tại Ocean Park 1."
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
                "conversation_mode": (
                    "deterministic_social"
                    if decision.intent in {"greeting", "social"}
                    else None
                ),
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
        # Compatibility-only lock: no caller may re-introduce an Agent/LLM
        # rewrite for a social decision. The public endpoint short-circuits
        # before this helper; direct calls still fail closed deterministically.
        del agent_result
        return cls.deterministic_response(decision, request_id=request_id)

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
            "tool_arguments": [],
            "proposal_id": None,
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
        try:
            from app.services.spatial_registry import spatial_registry
            if spatial_registry.find_poi_by_name(plain):
                return True
            _, unrec = spatial_registry.extract_location_in_query(plain)
            if unrec:
                return True
        except Exception:
            pass
        has_context = bool(station_id) or bool(
            map_context
            and any(map_context.get(key) for key in ("selected_sensor", "selected_location", "user_location"))
        )
        # A distance-only follow-up after a route suggestion is still a route request.
        # For example: "tôi chỉ muốn chạy 2km thôi" must adjust the route, not
        # fall through to the generic clarification response.
        if cls._DISTANCE_TARGET_RE.search(plain) and (
            any(cue in plain for cue in cls._RUNNING_DISTANCE_CUES) or has_context
        ):
            return True
        return has_context and any(signal in plain for signal in cls._CONTEXT_FOLLOW_UPS)

    @classmethod
    def _has_explicit_domain_request(cls, plain: str) -> bool:
        return cls._is_domain_query(plain, station_id=None, map_context=None)

    @staticmethod
    def _plain(value: str) -> str:
        normalized = unicodedata.normalize(
            "NFD", unicodedata.normalize("NFKC", value).lower().replace("đ", "d")
        )
        without_accents = "".join(
            character for character in normalized if unicodedata.category(character) != "Mn"
        )
        without_punctuation = re.sub(r"[^a-z0-9.\s]", " ", without_accents)
        return re.sub(r"\s+", " ", without_punctuation).strip()

    @classmethod
    def _social_plain(cls, value: str) -> str:
        # Strip all punctuation only after the domain-safe normalization. This
        # accepts trailing dots/ellipsis while leaving PM2.5 intact for routing.
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", cls._plain(value))).strip()


conversational_agent = ConversationalAgentService()
