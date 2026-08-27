from __future__ import annotations

import asyncio
import json
import re
from time import perf_counter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from src.agents.policies.grounding import (
    Intent,
    RouteDecision,
    _conversation_station_ids,
    _is_memory_follow_up,
    _plain,
    _stations,
)
from src.agents.tools.contracts import ToolName
from src.config import get_settings
from src.services.llm import (
    LlmProviderError,
    get_llm,
    normalize_llm_exception,
    resolve_llm_provider,
    resolved_model_name,
)


class SemanticRoute(BaseModel):
    """LLM proposal for routing only; never contains environmental values."""

    model_config = ConfigDict(extra="forbid")

    intent: Literal[
        "current",
        "compare",
        "history",
        "forecast",
        "active_alerts",
        "weather",
        "recommendation",
        "clarification",
        "out_of_scope",
    ]
    station_ids: list[str] = Field(default_factory=list, max_length=5)
    hours: int | None = Field(default=None, ge=1, le=72)
    metric: Literal["aqi", "pm25"] | None = None
    comparison_mode: Literal["highest_aqi", "lowest_aqi"] | None = None
    confidence: float = Field(ge=0, le=1)
    needs_clarification: bool = False

    @field_validator("station_ids")
    @classmethod
    def station_ids_are_allowlisted(cls, values: list[str]) -> list[str]:
        normalized = [value.upper() for value in values]
        if any(not re.fullmatch(r"S0[1-5]", value) for value in normalized):
            raise ValueError("station_ids must be limited to S01-S05")
        if len(set(normalized)) != len(normalized):
            raise ValueError("station_ids must be unique")
        return normalized

    @model_validator(mode="after")
    def fields_match_intent(self) -> SemanticRoute:
        if self.intent == "forecast" and self.hours is None:
            raise ValueError("forecast requires hours")
        if self.intent in {"forecast", "recommendation"} and self.hours is not None and self.hours > 3:
            raise ValueError("forecast and recommendation hours must be within 1-3")
        if self.intent != "forecast" and self.metric is not None:
            raise ValueError("metric is only valid for forecast")
        if self.intent not in {"forecast", "recommendation"} and self.hours is not None:
            raise ValueError("hours is only valid for forecast or recommendation")
        if self.intent != "compare" and self.comparison_mode is not None:
            raise ValueError("comparison_mode is only valid for compare")
        return self


SEMANTIC_ROUTER_PROMPT = """You are a strict intent classifier for AirGuard environmental monitoring.
Return ONLY one JSON object, with exactly these keys:
intent, station_ids, hours, metric, comparison_mode, confidence, needs_clarification.

Allowed intent values: current, compare, history, forecast, active_alerts, weather,
recommendation, clarification, out_of_scope.
station_ids may contain only S01, S02, S03, S04, S05. Never return sensor values,
AQI numbers, timestamps, source names, user profile facts, or tool names.

Interpretation rules:
- A station id alone means current snapshot for that station.
- best/cleanest/most suitable station means compare all stations using lowest_aqi.
- worst/most polluted station means compare all stations using highest_aqi.
- compare two or more named stations means compare; use comparison_mode only when the
  user explicitly asks better/worse/cleaner/more polluted.
- forecast is only valid for 1-3 hours; use clarification when horizon is missing or
  outside that range. History means past/recent trend, not future.
- recommendation means the user asks what activity/action is suitable.
- If intent or station context is genuinely unclear, set needs_clarification=true.
- Out-of-scope requests are not AirGuard environmental requests.

User message:
"""


def _extract_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("semantic_router_invalid_json")
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("semantic_router_json_object_required")
    return payload


def _reply_text(reply: Any) -> str:
    content = getattr(reply, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("text")
        )
    return str(content or "")


async def classify_semantically(
    query: str,
    *,
    user_id: str | None = None,
    context_station_id: str | None = None,
    conversation_context: dict[str, Any] | None = None,
    settings: Any | None = None,
    telemetry: dict[str, Any] | None = None,
) -> RouteDecision | None:
    """Return a validated route proposal, or None on provider/contract failure."""
    observation = telemetry if telemetry is not None else {}
    observation.clear()
    observation.update({"llm_call_count": 0, "llm_stage": "semantic_router"})
    settings = settings or get_settings()
    if not getattr(settings, "semantic_router_enabled", True):
        observation["semantic_router_outcome"] = "disabled"
        return None
    provider = resolve_llm_provider(settings)
    if provider is None:
        observation["semantic_router_outcome"] = "provider_unavailable"
        return None
    observation.update(
        {
            "provider": provider,
            "model": resolved_model_name(settings, provider),
        }
    )
    started: float | None = None
    try:
        router_settings = (
            settings.model_copy(
                update={
                    "llm_temperature": 0.0,
                    "llm_max_tokens": 180,
                    "gemini_max_tokens": 180,
                    # Routing is optional and bounded to one logical invocation.
                    # Provider adapters must not retry this path and consume
                    # additional tokens behind the graph's call counter.
                    "llm_max_retries": 0,
                }
            )
            if hasattr(settings, "model_copy")
            else settings
        )
        llm = get_llm(settings=router_settings)
        deadline = float(getattr(settings, "semantic_router_deadline_seconds", 2.0))
        observation["llm_call_count"] = 1
        started = perf_counter()
        memory_stations = _conversation_station_ids(conversation_context)
        semantic_input = query
        if _is_memory_follow_up(_plain(query), memory_stations):
            last_intent = str((conversation_context or {}).get("last_intent") or "none")
            semantic_input += (
                "\nBackend-validated conversation station ids: "
                + ", ".join(memory_stations)
                + f". Previous intent: {last_intent}."
            )
        reply = await asyncio.wait_for(
            llm.ainvoke(SEMANTIC_ROUTER_PROMPT + semantic_input),
            timeout=deadline,
        )
        usage = getattr(reply, "usage_metadata", None) or {}
        token_usage = {
            key: int(value)
            for key, value in usage.items()
            if key in {"input_tokens", "output_tokens", "total_tokens"}
            and isinstance(value, (int, float))
        }
        if token_usage:
            observation["token_usage"] = token_usage
        proposal = SemanticRoute.model_validate(_extract_json(_reply_text(reply)))
    except asyncio.CancelledError:
        raise
    except LlmProviderError as exc:
        observation["semantic_router_outcome"] = "failed"
        observation["failure_code"] = str(exc)
        return None
    except TimeoutError:
        observation["semantic_router_outcome"] = "failed"
        observation["failure_code"] = "provider_timeout"
        return None
    except (ValidationError, ValueError, TypeError, AttributeError):
        observation["semantic_router_outcome"] = "failed"
        observation["failure_code"] = "semantic_router_invalid_response"
        return None
    except Exception as exc:
        observation["semantic_router_outcome"] = "failed"
        observation["failure_code"] = str(normalize_llm_exception(exc))
        return None
    finally:
        if started is not None:
            observation["llm_latency_ms"] = round((perf_counter() - started) * 1000, 3)

    threshold = float(getattr(settings, "semantic_router_confidence_threshold", 0.8))
    if proposal.confidence < threshold or proposal.needs_clarification:
        observation["semantic_router_outcome"] = "rejected"
        return None
    decision = _route_from_proposal(
        proposal,
        query,
        user_id=user_id,
        context_station_id=context_station_id,
        conversation_context=conversation_context,
    )
    if decision is not None:
        decision.routing_mode = "semantic"
        decision.semantic_confidence = proposal.confidence
        observation["semantic_router_outcome"] = "accepted"
    else:
        observation["semantic_router_outcome"] = "rejected"
    return decision


def _route_from_proposal(
    proposal: SemanticRoute,
    query: str,
    *,
    user_id: str | None = None,
    context_station_id: str | None = None,
    conversation_context: dict[str, Any] | None = None,
) -> RouteDecision | None:
    explicit_stations = _stations(query)
    if re.search(r"\bS\d{2}\b", query.upper()) and not explicit_stations:
        return None
    validated_context = (
        context_station_id.upper()
        if context_station_id and re.fullmatch(r"S0[1-5]", context_station_id.upper())
        else None
    )
    allowed_request_stations = set(explicit_stations)
    if not explicit_stations and validated_context:
        allowed_request_stations.add(validated_context)
    memory_stations = _conversation_station_ids(conversation_context)
    memory_follow_up = _is_memory_follow_up(_plain(query), memory_stations)
    if memory_follow_up:
        allowed_request_stations.update(memory_stations)
    proposed_stations = proposal.station_ids
    all_station_compare = (
        proposal.intent == "compare"
        and proposal.comparison_mode is not None
        and not explicit_stations
    )
    if all_station_compare and proposed_stations and set(proposed_stations) != {
        "S01", "S02", "S03", "S04", "S05"
    }:
        # A superlative without explicit station ids is a map-wide question;
        # never let the model silently narrow it to a guessed subset.
        return None
    if proposed_stations and not all_station_compare and not set(proposed_stations).issubset(allowed_request_stations):
        return None
    stations = (
        proposed_stations
        or explicit_stations
        or (memory_stations if memory_follow_up else [])
        or ([validated_context] if validated_context else [])
    )
    if proposal.intent in {"clarification", "out_of_scope"}:
        return None
    if proposal.intent == "current":
        if len(stations) != 1:
            return None
        return RouteDecision(
            intent=Intent.CURRENT,
            tool_calls=[ToolName.GET_CURRENT_PM25],
            tool_arguments=[{"station_id": stations[0]}],
        )
    if proposal.intent == "compare":
        if len(stations) < 2:
            stations = ["S01", "S02", "S03", "S04", "S05"] if proposal.comparison_mode else stations
        if len(stations) < 2:
            return None
        return RouteDecision(
            intent=Intent.COMPARE,
            tool_calls=[ToolName.COMPARE_STATIONS],
            tool_arguments=[{"station_ids": stations}],
            comparison_mode=proposal.comparison_mode,
        )
    if proposal.intent == "history":
        if len(stations) != 1:
            return None
        return RouteDecision(
            intent=Intent.HISTORY,
            tool_calls=[ToolName.GET_STATION_HISTORY],
            tool_arguments=[{"station_id": stations[0], "hours": proposal.hours or 24}],
        )
    if proposal.intent == "forecast":
        if len(stations) != 1 or proposal.hours is None:
            return None
        return RouteDecision(
            intent=Intent.FORECAST,
            tool_calls=[ToolName.GET_PM25_FORECAST],
            tool_arguments=[{"station_id": stations[0], "hours": proposal.hours, "metric": proposal.metric or "pm25"}],
        )
    if proposal.intent == "active_alerts":
        if len(stations) > 1:
            return None
        return RouteDecision(
            intent=Intent.ACTIVE_ALERTS,
            tool_calls=[ToolName.GET_ACTIVE_ALERTS],
            tool_arguments=[{"station_id": stations[0]} if stations else {}],
        )
    if proposal.intent == "weather":
        return RouteDecision(
            intent=Intent.WEATHER,
            tool_calls=[ToolName.GET_WEATHER_CONTEXT],
            tool_arguments=[{}],
        )
    if proposal.intent == "recommendation":
        if len(stations) != 1 or not user_id:
            return None
        return RouteDecision(
            intent=Intent.RECOMMENDATION,
            tool_calls=[
                ToolName.GET_USER_PROFILE,
                ToolName.GET_CURRENT_PM25,
                ToolName.GET_WEATHER_CONTEXT,
                ToolName.GET_PM25_FORECAST,
                ToolName.GET_ACTIVE_ALERTS,
            ],
            tool_arguments=[
                {"user_id": user_id},
                {"station_id": stations[0]},
                {},
                {"station_id": stations[0], "hours": proposal.hours or 3, "metric": "pm25"},
                {"station_id": stations[0]},
            ],
        )
    return None
