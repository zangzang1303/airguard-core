from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx


@dataclass(frozen=True)
class NarrativeResult:
    narrative: str
    generation_mode: str
    model_source: str
    claims: tuple[dict[str, str], ...] = ()


class ReportNarrator(Protocol):
    def generate(self, evidence_summary: dict[str, Any]) -> NarrativeResult: ...


class NarrativeServiceError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


_SENSITIVE_KEY_PARTS = ("password", "token", "secret", "authorization", "api_key", "email", "user_id")
_EMAIL_PATTERN = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)
_SENTENCE_PATTERN = re.compile(r"[^.!?]+[.!?](?:\s+|$)")
_MODEL_SOURCE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,119}$")
_ALLOWED_CLAIM_TYPES = {
    "trend": "trends",
    "coverage": "coverage",
    "reference": "reference_comparison",
    "acknowledged_activity": "acknowledged_activity",
    "estimate_availability": "esg_metrics",
}
_UNSAFE_CLAIM_MARKERS = (
    "because",
    "caused",
    "causes",
    "due to",
    "compliant",
    "compliance",
    "certified",
    "meets the standard",
    "health benefit",
    "healthier",
    "prevents disease",
    "removed",
    "saved",
)


def validate_aggregate_evidence(value: Any, *, path: str = "evidence") -> None:
    """Reject PII/secret-shaped material before it can cross the LLM boundary."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower()
            if any(marker in normalized for marker in _SENSITIVE_KEY_PARTS):
                raise NarrativeServiceError("unsafe_evidence_key")
            validate_aggregate_evidence(item, path=f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_aggregate_evidence(item, path=f"{path}[{index}]")
        return
    if isinstance(value, str) and (_EMAIL_PATTERN.search(value) or _URL_PATTERN.search(value)):
        raise NarrativeServiceError("unsafe_evidence_value")


def validate_live_narrative(value: Any) -> str:
    """Accept qualitative prose only; all quantitative statements remain backend-owned."""
    if not isinstance(value, str):
        raise NarrativeServiceError("narrative_schema_invalid")
    narrative = " ".join(value.split()).strip()
    if not narrative:
        raise NarrativeServiceError("narrative_empty")
    sentences = _SENTENCE_PATTERN.findall(narrative)
    if len(sentences) < 3 or len(sentences) > 5:
        raise NarrativeServiceError("narrative_sentence_count_invalid")
    lowered = narrative.lower()
    if (
        any(character.isdigit() for character in narrative)
        or _EMAIL_PATTERN.search(narrative)
        or _URL_PATTERN.search(narrative)
        or "<" in narrative
        or ">" in narrative
        or any(marker in lowered for marker in _SENSITIVE_KEY_PARTS)
        or any(marker in lowered for marker in _UNSAFE_CLAIM_MARKERS)
    ):
        raise NarrativeServiceError("narrative_not_qualitative")
    return narrative


def validate_typed_claims(value: Any, evidence_summary: dict[str, Any]) -> tuple[str, tuple[dict[str, str], ...]]:
    if not isinstance(value, list) or not 3 <= len(value) <= 5:
        raise NarrativeServiceError("narrative_schema_invalid")
    allowed = evidence_summary.get("allowed_claim_types")
    if not isinstance(allowed, list):
        raise NarrativeServiceError("narrative_evidence_allow_list_missing")
    accepted: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"claim_type", "text"}:
            raise NarrativeServiceError("narrative_schema_invalid")
        claim_type = str(item.get("claim_type") or "")
        if claim_type not in _ALLOWED_CLAIM_TYPES or claim_type not in allowed:
            raise NarrativeServiceError("narrative_claim_type_not_allowed")
        evidence_key = _ALLOWED_CLAIM_TYPES[claim_type]
        if not evidence_summary.get(evidence_key):
            raise NarrativeServiceError("narrative_claim_evidence_missing")
        text = validate_live_narrative_sentence(item.get("text"))
        accepted.append({"claim_type": claim_type, "text": text})
    narrative = validate_live_narrative(" ".join(item["text"] for item in accepted))
    return narrative, tuple(accepted)


def validate_live_narrative_sentence(value: Any) -> str:
    if not isinstance(value, str):
        raise NarrativeServiceError("narrative_schema_invalid")
    sentence = " ".join(value.split()).strip()
    if not sentence or not re.fullmatch(r"[^.!?]+[.!?]", sentence):
        raise NarrativeServiceError("narrative_schema_invalid")
    lowered = sentence.lower()
    if (
        any(character.isdigit() for character in sentence)
        or _EMAIL_PATTERN.search(sentence)
        or _URL_PATTERN.search(sentence)
        or "<" in sentence
        or ">" in sentence
        or any(marker in lowered for marker in _SENSITIVE_KEY_PARTS)
        or any(marker in lowered for marker in _UNSAFE_CLAIM_MARKERS)
    ):
        raise NarrativeServiceError("narrative_not_qualitative")
    return sentence


def validate_model_source(value: Any) -> str:
    if not isinstance(value, str) or not _MODEL_SOURCE_PATTERN.fullmatch(value.strip()):
        raise NarrativeServiceError("narrative_model_source_invalid")
    return value.strip()


class HttpReportNarrator:
    """Optional internal LLM narrator.

    The endpoint receives aggregate evidence only. It must return qualitative prose and
    explicitly label a successful provider result as ``live_llm``.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        timeout_seconds: float = 5.0,
        service_token: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not endpoint.strip():
            raise ValueError("endpoint is required")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.service_token = service_token
        self.transport = transport

    def generate(self, evidence_summary: dict[str, Any]) -> NarrativeResult:
        validate_aggregate_evidence(evidence_summary)
        headers = {"Content-Type": "application/json"}
        if self.service_token:
            headers["Authorization"] = f"Bearer {self.service_token}"
        try:
            with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = client.post(
                    self.endpoint,
                    json={"evidence_summary": evidence_summary},
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise NarrativeServiceError("narrative_provider_timeout") from exc
        except httpx.HTTPError as exc:
            raise NarrativeServiceError("narrative_provider_unavailable") from exc
        if response.status_code >= 400:
            raise NarrativeServiceError("narrative_provider_rejected")
        try:
            payload = response.json()
        except ValueError as exc:
            raise NarrativeServiceError("narrative_provider_invalid_json") from exc
        if not isinstance(payload, dict):
            raise NarrativeServiceError("narrative_provider_not_live")
        narrative, claims = validate_typed_claims(payload.get("sentences"), evidence_summary)
        model_source = validate_model_source(payload.get("model_source"))
        return NarrativeResult(
            narrative=narrative,
            generation_mode="live_llm",
            model_source=model_source,
            claims=claims,
        )
