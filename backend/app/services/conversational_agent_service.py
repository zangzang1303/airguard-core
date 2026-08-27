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


CAPABILITIES_RESPONSE = (
    "Mình hỗ trợ AQI/trạm hiện tại, so sánh trạm, dự báo baseline 1–3 giờ, cảnh báo, "
    "gợi ý lộ trình chạy bộ và khuyến nghị grounded từ dữ liệu demo/mô phỏng. "
    "AirGuard không dự báo dài hạn, chẩn đoán hay điều khiển thiết bị."
)


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
    _IDENTITY = {
        "ban bao nhieu tuoi",
        "ban may tuoi",
        "airguard bao nhieu tuoi",
        "airguard may tuoi",
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
        "do am",
        "nang",
        "gio",
        "tram",
        "sensor",
        "canh bao",
        "vuot nguong",
        "bat thuong",
        "co van de",
        "du bao",
        "du kien",
        "sap toi",
        "gio nua",
        "tiep theo",
        "hien tai",
        "ra sao",
        "tinh hinh",
        "gan day",
        "dien bien",
        "thay doi",
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
        "doi chieu",
        "tot hon",
        "sach hon",
        "on hon",
        "it o nhiem hon",
        "tram tot nhat",
        "tram on nhat",
        "tram sach nhat",
        "tram o nhiem nhat",
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
        "uong thuoc",
        "thuoc gi",
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
    def _is_capability_query(cls, plain: str, social_plain: str) -> bool:
        if social_plain in cls._CAPABILITIES:
            return True
        if re.search(
            r"\b(?:ngoai|tru)\s+(?:chay\s*bo|chay|di\s*bo|cung\s*duong|lo\s*trinh|ban\s*do|thoi\s*tiet|aqi|pm25)?.*?\b(?:lam\s*(?:duoc\s*)?gi|co\s*the\s*lam\s*gi|giup\s*(?:duoc\s*)?gi|chuc\s*nang\s*gi|tinh\s*nang\s*gi|ho\s*tro\s*gi|con\s*gi\s*khac|gi\s*khac|lam\s*gi\s*khac)\b",
            plain,
        ):
            return True
        if re.search(
            r"\b(?:co\s*the\s*lam\s*gi\s*khac|lam\s*duoc\s*gi\s*khac|giup\s*duoc\s*gi\s*khac|chuc\s*nang\s*gi\s*khac|tinh\s*nang\s*gi\s*khac|con\s*lam\s*(?:duoc\s*)?gi|con\s*gi\s*khac|con\s*tinh\s*nang\s*gi|con\s*chuc\s*nang\s*gi)\b",
            plain,
        ):
            return True
        if re.search(
            r"\b(?:ban|airguard|bot|ai|tro\s*ly)\s+(?:la\s*ai|la\s*gi|lam\s*duoc\s*gi|co\s*the\s*lam\s*gi|co\s*the\s*giup\s*gi|giup\s*duoc\s*gi|ho\s*tro\s*duoc\s*gi|co\s*chuc\s*nang\s*gi|co\s*tinh\s*nang\s*gi|biet\s*lam\s*gi)\b",
            plain,
        ):
            return True
        if re.search(
            r"\b(?:chuc\s*nang|tinh\s*nang|kha\s*nang)\s+cua\s+(?:ban|airguard|bot|ai|tro\s*ly|he\s*thong|app)\b",
            plain,
        ):
            return True
        if re.search(
            r"\b(?:huong\s*dan\s*su\s*dung|cach\s*su\s*dung|dung\s*de\s*lam\s*gi|ung\s*dung\s*nay\s*dung\s*de\s*lam\s*gi)\b",
            plain,
        ):
            return True
        return False

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
        if cls._is_capability_query(plain, social_plain):
            has_station = bool(re.search(r"\bS0[1-5]\b", plain.upper()))
            has_metric = any(m in plain for m in ("pm2.5", "pm25", "aqi", "co2", "nhiet do", "tieng on", "canh bao", "du bao"))
            if not (has_station and has_metric):
                return ConversationDecision(
                    intent="social",
                    kind="capabilities",
                    fallback_response=CAPABILITIES_RESPONSE,
                )

        if cls._contains_phrase(plain, cls._OUT_OF_SCOPE_SIGNALS):
            return ConversationDecision(
                intent="out_of_scope",
                kind="out_of_scope",
                fallback_response=(
                    "Yêu cầu này nằm ngoài phạm vi quan trắc của hệ thống AirGuard AI. "
                    "AirGuard là hệ thống chuyên về giám sát chất lượng không khí (AQI, PM2.5, CO₂), "
                    "cảnh báo môi trường và gợi ý lộ trình vận động ngoài trời tại Ocean Park 1."
                ),
            )
        if social_plain in cls._IDENTITY:
            return ConversationDecision(
                intent="social",
                kind="identity",
                fallback_response=(
                    "Mình là trợ lý AI nên không có tuổi như con người. Mình có thể hỗ trợ các câu hỏi AirGuard."
                ),
            )

        # A concrete environmental request always wins over a social prefix.
        if cls._has_explicit_domain_request(plain):
            return ConversationDecision(intent="domain", kind="domain", fallback_response="")

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
        if cls._DISTANCE_TARGET_RE.search(plain) and (
            any(cue in plain for cue in cls._RUNNING_DISTANCE_CUES) or has_context
        ):
            return True
        return has_context and any(signal in plain for signal in cls._CONTEXT_FOLLOW_UPS)

    @classmethod
    def _has_explicit_domain_request(cls, plain: str) -> bool:
        social_plain = cls._social_plain(plain)
        if cls._is_capability_query(plain, social_plain):
            has_station = bool(re.search(r"\bS0[1-5]\b", plain.upper()))
            has_metric = any(m in plain for m in ("pm2.5", "pm25", "aqi", "co2", "nhiet do", "tieng on", "canh bao", "du bao"))
            if not (has_station and has_metric):
                return False
        return cls._is_domain_query(plain, station_id=None, map_context=None)

    @staticmethod
    def _contains_phrase(value: str, phrases: tuple[str, ...]) -> bool:
        return any(re.search(rf"\b{re.escape(phrase)}\b", value) for phrase in phrases)

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
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", cls._plain(value))).strip()


conversational_agent = ConversationalAgentService()
