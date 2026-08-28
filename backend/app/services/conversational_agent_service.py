from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal

ConversationIntent = Literal[
    "domain",
    "social.greeting",
    "social.assistant_identity",
    "social.smalltalk",
    "conversation.capability",
    "conversation.unknown",
    "out_of_scope",
    "greeting",
    "social",
    "clarification",
]


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

    _IDENTITY_AGE = {
        "ban bao tuoi",
        "ban bao nhieu tuoi",
        "ban may tuoi",
        "bao tuoi",
        "bao nhieu tuoi",
        "may tuoi",
        "tuoi cua ban",
        "tuoi ban",
        "tuoi gi",
        "ban bao nhieu tuoi roi",
        "ban duoc bao nhieu tuoi",
        "how old are you",
        "what is your age",
        "your age",
    }
    _IDENTITY_WHO = {
        "ban la ai",
        "ban ten gi",
        "ten ban la gi",
        "ai tao ra ban",
        "ai lam ra ban",
        "ban la nguoi hay ai",
        "ban la nguoi hay bot",
        "ban la robot a",
        "ban la robot ha",
        "ban co phai con nguoi khong",
        "ban la gi",
        "who are you",
        "what is your name",
        "who made you",
    }
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
        "chao buoi sang",
        "chao buoi toi",
        "chao buoi chieu",
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
        "tuyet voi",
        "hay day",
        "cam on nha",
        "thanks ban",
    }
    _FAREWELLS = {"tam biet", "bye", "goodbye", "hen gap lai", "chao nhe", "bye bye"}
    _WELLBEING = {
        "khoe khong",
        "ban khoe khong",
        "ban co khoe khong",
        "hom nay the nao",
        "hom nay ban the nao",
        "airguard khoe khong",
        "airguard co khoe khong",
        "how are you",
        "dao nay the nao",
    }
    _CAPABILITIES = {
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
        "toi co the hoi gi",
        "toi co the hoi nhung gi",
        "hoi duoc gi",
        "ban co chuc nang gi",
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
        "mua bao",
        "con bao",
        "do am",
        "nang",
        "gio",
        "tram quan trac",
        "sensor",
        "canh bao",
        "du bao",
        "hien tai",
        "toi nay",
        "chieu nay",
        "sang nay",
        "cho nay",
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
        "sach nhat",
        "tot nhat",
        "o nhiem nhat",
        "xau nhat",
        "tranh",
        "toan khu",
        "ca khu",
        "tong quan",
        "tinh hinh chung",
        "khong khi chung",
        "nhom nhay cam",
        "nhay cam",
        "sensitive group",
        "nen lam gi",
        "o nhiem",
        "trong nha",
        "indoor",
        "gym",
        "fitness",
        "dap xe",
        "xe dap",
    )
    _CONTEXT_FOLLOW_UPS = (
        "o day",
        "cho nay",
        "khu nay",
        "o do",
        "cho do",
        "khu do",
        "noi do",
        "toi do",
        "den do",
        "di toi do",
        "the nao",
        "toi nay",
        "hom nay",
        "bay gio",
        "aqi bao nhieu",
        "pm25 bao nhieu",
        "bao nhieu do",
        "nhiet do bao nhieu",
        "chi so bao nhieu",
        "co tot",
        "co nen",
        "trong nha",
        "gym",
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
        conversation_id: str = "",
    ) -> ConversationDecision:
        plain = cls._plain(message)
        social_plain = cls._social_plain(message)

        # 0. Check dialogue state resolution (Pending actions, awaiting slots, modifications)
        if conversation_id:
            try:
                from .conversation_state_manager import conversation_state_manager
                turn_res = conversation_state_manager.resolve_conversation_turn(
                    conversation_id, message, map_context, peek=True
                )
                if turn_res["resolution_type"] in {"accept_pending_action", "answer_slot", "modify", "reference"}:
                    return ConversationDecision(intent="domain", kind=turn_res["resolution_type"], fallback_response="")
                if turn_res["resolution_type"] == "reject_pending_action":
                    conversation_state_manager.clear_pending_action(conversation_id)
                    conversation_state_manager.clear_awaiting_slot(conversation_id)
                    return ConversationDecision(
                        intent="social.smalltalk",
                        kind="action_cancelled",
                        fallback_response="👌 **Đã hủy đề xuất.**\n\nNếu cần hỗ trợ thêm về chất lượng không khí, địa điểm hay lộ trình tại Ocean Park 1, bạn cứ nhắn mình nhé!",
                    )
            except Exception:
                pass

        # 1. Explicit domain requests always win over a social prefix
        if cls._has_explicit_domain_request(plain):
            return ConversationDecision(intent="domain", kind="domain", fallback_response="")

        # 2. Assistant Identity: Age questions (Rule 2: Social/Identity has high priority)
        if social_plain in cls._IDENTITY_AGE or any(pat in social_plain for pat in ["bao nhieu tuoi", "bao tuoi", "may tuoi", "how old are you", "tuoi cua ban"]):
            return ConversationDecision(
                intent="social.assistant_identity",
                kind="identity_age",
                fallback_response=(
                    "Mình là trợ lý AI nên không có tuổi như con người 😊\n\n"
                    "Mình được thiết kế để hỗ trợ bạn về chất lượng không khí, địa điểm và lộ trình trong Vinhomes Ocean Park 1."
                ),
            )

        # 3. Assistant Identity: Who/Name/Creator questions
        if social_plain in cls._IDENTITY_WHO or any(pat in social_plain for pat in ["ban la ai", "ban ten gi", "ai tao ra ban", "ban la nguoi hay ai", "who are you", "what is your name"]):
            return ConversationDecision(
                intent="social.assistant_identity",
                kind="identity_who",
                fallback_response=(
                    "Mình là **AirGuard Geospatial AI**, trợ lý AI hỗ trợ bạn kiểm tra chất lượng không khí, địa điểm và lộ trình trong Vinhomes Ocean Park 1."
                ),
            )

        # 4. Capabilities (e.g. "bạn làm được gì", "bạn giúp được gì ở đây")
        if social_plain in cls._CAPABILITIES or any(pat in social_plain for pat in ["ban lam duoc gi", "ban giup duoc gi", "ban co the lam gi", "toi co the hoi gi", "ban giup gi", "giup gi"]):
            return ConversationDecision(
                intent="conversation.capability",
                kind="capabilities",
                fallback_response=(
                    "Mình có thể giúp bạn:\n"
                    "• Kiểm tra chất lượng không khí theo từng khu vực tại Ocean Park 1\n"
                    "• So sánh chất lượng không khí giữa các địa điểm\n"
                    "• Xem dự báo AQI ngắn hạn 1–3 giờ\n"
                    "• Tìm cung đường đi bộ/chạy bộ tối ưu mức độ trong lành\n"
                    "• Định vị và hiển thị kết quả trực quan trên bản đồ"
                ),
            )

        # 5. Greetings
        if social_plain in cls._GREETINGS or any(social_plain.startswith(g + " ") for g in ["xin chao", "chao ban", "hello", "hi"]):
            return ConversationDecision(
                intent="social.greeting",
                kind="greeting",
                fallback_response=(
                    "Mình đây 👋 Bạn muốn kiểm tra chất lượng không khí, so sánh khu vực "
                    "hay tìm cung đường chạy bộ trong Ocean Park 1?"
                ),
            )

        # 6. Acknowledgements & Thanks
        if social_plain in cls._THANKS_AND_ACKS or any(social_plain.startswith(t + " ") for t in ["cam on", "thank you", "thanks"]):
            return ConversationDecision(
                intent="social.smalltalk",
                kind="acknowledgement",
                fallback_response="Không có gì 😊 Nếu cần, bạn cứ hỏi mình về không khí hoặc địa điểm trong Ocean Park 1 nhé!",
            )

        # 7. Farewells
        if social_plain in cls._FAREWELLS or any(f in social_plain for f in ["tam biet", "hen gap lai", "chao nhe", "bye bye", "goodbye"]):
            return ConversationDecision(
                intent="social.smalltalk",
                kind="farewell",
                fallback_response="Tạm biệt bạn! Hẹn gặp lại khi bạn cần hỗ trợ từ AirGuard 👋",
            )

        # 8. Wellbeing
        if social_plain in cls._WELLBEING or any(w in social_plain for w in ["khoe khong", "ban khoe khong", "hom nay the nao", "how are you"]):
            return ConversationDecision(
                intent="social.smalltalk",
                kind="wellbeing",
                fallback_response=(
                    "Mình là trợ lý AI nên luôn sẵn sàng hoạt động để hỗ trợ bạn! Hôm nay bạn muốn kiểm tra khu vực nào ở Ocean Park 1 không?"
                ),
            )

        # 9. Out of Scope
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

        # 10. Domain Boundary
        if cls._is_domain_query(plain, station_id=station_id, map_context=map_context):
            return ConversationDecision(intent="domain", kind="domain", fallback_response="")

        # 11. Unknown / Clarification
        return ConversationDecision(
            intent="conversation.unknown",
            kind="unclear",
            fallback_response=(
                "Bạn muốn mình kiểm tra **chất lượng không khí**, **một địa điểm**, hay **một cung đường** trong Ocean Park 1?"
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
                    if (
                        decision.intent in {"greeting", "social"}
                        or decision.intent.startswith("social.")
                        or decision.intent == "conversation.capability"
                    )
                    else None
                ),
                "final_outcome": (
                    "clarification"
                    if decision.intent in {"clarification", "conversation.unknown"}
                    else "direct_response"
                ),
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
