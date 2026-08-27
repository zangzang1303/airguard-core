from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import uuid4

from src.agents.policies.grounding import GROUNDING_POLICY_VERSION, Intent, RouteDecision, route_query
from src.agents.policies.impact_assessment import IMPACT_POLICY_VERSION
from src.agents.policies.proposal_eligibility import PROPOSAL_POLICY_VERSION
from src.agents.policies.recommendations import RECOMMENDATION_POLICY_VERSION
from src.agents.policies.semantic_router import classify_semantically
from src.agents.response_composer import compose_response
from src.agents.state import AgentState
from src.agents.tools.contracts import ToolError, ToolErrorCode, ToolName
from src.agents.trace import emit_trace
from src.config import get_settings


async def route_node(state: AgentState) -> dict[str, Any]:
    request_id = state.get("request_id") or f"agent-{uuid4()}"
    started_at = perf_counter()
    decision = route_query(
        state.get("query", ""),
        context_station_id=state.get("context_station_id"),
        user_id=state.get("user_id"),
    )
    # Semantic routing is a bounded fallback for genuinely unclear requests.
    # Safety/social decisions never reach the provider. The semantic router
    # returns a typed decision only after schema and allowlist validation.
    if (
        decision.intent in {Intent.CLARIFICATION, Intent.OUT_OF_SCOPE}
        and decision.safety_category is None
        and decision.conversation_kind is None
    ):
        llm_observation: dict[str, Any] = {}
        semantic_decision = await classify_semantically(
            state.get("query", ""),
            user_id=state.get("user_id"),
            context_station_id=state.get("context_station_id"),
            settings=get_settings(),
            telemetry=llm_observation,
        )
        if semantic_decision is not None:
            decision = semantic_decision
    else:
        llm_observation = {"llm_call_count": 0}
    return {
        "request_id": request_id,
        "started_at": started_at,
        "route": decision.model_dump(mode="json"),
        "analysis": f"intent={decision.intent.value}",
        "tool_results": [],
        "tool_traces": [],
        "used_tools": [],
        "llm_observation": llm_observation,
    }


def route_after_intent(state: AgentState) -> str:
    decision = RouteDecision.model_validate(state["route"])
    if decision.direct_response is not None:
        return "compose"
    if decision.intent == Intent.PROPOSAL:
        return "create_proposal"
    return "execute_tools" if decision.requires_tools else "compose"


async def execute_tools_node(state: AgentState, *, tool_client: Any) -> dict[str, Any]:
    decision = RouteDecision.model_validate(state["route"])
    request_id = state["request_id"]
    results: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    used_tools: list[str] = []

    planned_calls = list(zip(decision.tool_calls, decision.tool_arguments, strict=True))
    call_index = 0
    while call_index < len(planned_calls):
        tool_name, arguments = planned_calls[call_index]
        call_index += 1
        used_tools.append(tool_name.value)
        started_at = perf_counter()
        try:
            method = getattr(tool_client, tool_name.value)
            result = await method(arguments, request_id=request_id)
        except Exception as exc:  # Adapter boundaries must fail closed.
            result = ToolError(
                tool_name=tool_name,
                code=ToolErrorCode.UNAVAILABLE,
                message="Tool adapter failed safely.",
                request_id=request_id,
                details={"error_type": exc.__class__.__name__},
            )
        latency_ms = round((perf_counter() - started_at) * 1000, 3)
        serialized = result.model_dump(mode="json")
        results.append(serialized)
        traces.append(
            {
                "tool_name": tool_name.value,
                "status": "success" if result.ok else result.code.value,
                "latency_ms": latency_ms,
            }
        )

        if decision.intent == Intent.RECOMMENDATION and tool_name == ToolName.GET_USER_PROFILE:
            if not result.ok:
                break
            if result.data.get("group") == "outdoor_sport":
                comparison_arguments = {"station_ids": ["S01", "S02", "S03", "S04", "S05"]}
                planned_calls.append((ToolName.COMPARE_STATIONS, comparison_arguments))
                decision.tool_calls.append(ToolName.COMPARE_STATIONS)
                decision.tool_arguments.append(comparison_arguments)

    if decision.intent == Intent.RECOMMENDATION:
        composer_order = {
            ToolName.GET_CURRENT_PM25.value: 0,
            ToolName.GET_WEATHER_CONTEXT.value: 1,
            ToolName.GET_PM25_FORECAST.value: 2,
            ToolName.GET_ACTIVE_ALERTS.value: 3,
            ToolName.GET_USER_PROFILE.value: 4,
            ToolName.COMPARE_STATIONS.value: 5,
        }
        results.sort(key=lambda item: composer_order.get(str(item.get("tool_name")), 99))

    return {
        "route": decision.model_dump(mode="json"),
        "tool_results": results,
        "tool_traces": traces,
        "used_tools": used_tools,
    }


def compose_node(state: AgentState) -> dict[str, Any]:
    decision = RouteDecision.model_validate(state["route"])
    if decision.intent == Intent.PROPOSAL and decision.direct_response is None:
        outcome = state.get("outcome")
        reason = state.get("proposal_reason_code")
        proposal_id = state.get("proposal_id")
        if outcome == "created" and proposal_id:
            proposal_sources = [
                {
                    "tool_name": result.get("tool_name"),
                    "station_id": item.get("station_id"),
                    "source": item.get("source"),
                    "evidence_id": item.get("evidence_id"),
                }
                for result in state.get("tool_results", [])
                if result.get("ok") and result.get("tool_name") in {
                    ToolName.GET_CURRENT_PM25.value,
                    ToolName.GET_ACTIVE_ALERTS.value,
                }
                for item in ([result.get("data", {})] if result.get("tool_name") == ToolName.GET_CURRENT_PM25.value else result.get("data", {}).get("items", []))
                if item.get("source") or item.get("evidence_id")
            ]
            answer = (
                    f"Đã tạo warning proposal {proposal_id} ở trạng thái pending. "
                    "Manager cần review trước khi có bất kỳ lệnh thiết bị nào được dispatch."
                )
            return {
                "answer": answer,
                "answer_summary": answer,
                "answer_details": "Proposal chỉ được chuyển sang bước review HITL sau khi backend trả về trạng thái pending.",
                "response": f"Proposal {proposal_id} is pending manager review.",
                "sources": proposal_sources,
                "outcome": "proposal_pending",
                "proposal_id": proposal_id,
                "pending": True,
                "intent": decision.intent.value,
                "data_mode": _data_mode(state.get("tool_results", [])),
                "quality": "fresh",
                "failure_reason": None,
                "clarification": None,
            }
        answer = f"Không thể tạo warning proposal: {reason or 'insufficient_evidence'}."
        return {
            "answer": answer,
            "answer_summary": answer,
            "answer_details": "Không có proposal_id hoặc environmental source nào được tạo khi evidence/eligibility không hợp lệ.",
            "response": f"Warning proposal blocked: {reason or 'insufficient_evidence'}.",
            "sources": [],
            "outcome": outcome or "blocked",
            "intent": decision.intent.value,
            "data_mode": None,
            "quality": None,
            "failure_reason": reason or "insufficient_evidence",
            "clarification": None,
        }
    composed = compose_response(decision, state.get("tool_results", []))
    answer = composed["answer"]
    summary, details = _split_grounded_answer(decision, answer, composed["outcome"])
    result = {
        "answer": answer,
        "answer_summary": summary,
        "answer_details": details,
        "response": answer,
        "sources": composed["sources"],
        "outcome": composed["outcome"],
        "intent": decision.intent.value,
        "data_mode": _data_mode(state.get("tool_results", [])) if composed["sources"] else None,
        "quality": _quality_status(decision.intent, composed["outcome"], state.get("tool_results", [])),
        "failure_reason": _failure_reason(composed["outcome"], state.get("tool_results", [])),
        "clarification": composed["answer"] if composed["outcome"] == "clarification" else None,
    }
    if composed.get("recommendation_policy_version"):
        result["recommendation_policy_version"] = composed["recommendation_policy_version"]
    if decision.intent == Intent.IMPACT:
        result["impact_policy_version"] = IMPACT_POLICY_VERSION
    return result


def _split_grounded_answer(decision: RouteDecision, answer: str, outcome: str) -> tuple[str, str]:
    """Create additive presentation fields without changing grounded answer text.

    Facts remain exactly those produced by the deterministic composer. The split is
    deliberately conservative in Phase 2: direct/refusal/insufficient responses
    stay wholly in summary; environmental answers move provenance-heavy suffixes
    into details only when an explicit sentence boundary is available.
    """
    if not answer:
        return "", ""
    if outcome != "answered" or decision.intent in {
        Intent.CLARIFICATION,
        Intent.SAFETY_REFUSAL,
        Intent.OUT_OF_SCOPE,
        Intent.SOCIAL,
    }:
        return answer, ""
    if decision.intent == Intent.RECOMMENDATION:
        recommendation_marker = "Khuyến nghị cho nhóm "
        basis_marker = " Cơ sở:"
        marker_index = answer.find(recommendation_marker)
        if marker_index >= 0:
            end_index = answer.find(basis_marker, marker_index)
            if end_index < 0:
                end_index = answer.find(".", marker_index)
            if end_index > marker_index:
                action = answer[marker_index:end_index].strip().rstrip(".")
                station = ""
                station_marker = "Quan sát tại "
                station_index = answer.find(station_marker)
                if station_index >= 0:
                    station = answer[station_index + len(station_marker) :].split(":", 1)[0].strip()
                summary_prefix = f"Khuyến nghị tại {station}: " if station else "Khuyến nghị: "
                summary = summary_prefix + action.split(": ", 1)[-1].strip() + "."
                details = answer[:marker_index].strip() + " " + answer[end_index:].strip()
                return summary, details
    sentences = [part.strip() for part in answer.split(". ") if part.strip()]
    if len(sentences) <= 2:
        return answer, ""
    summary = ". ".join(sentences[:2]).rstrip(".") + "."
    details = ". ".join(sentences[2:]).strip()
    if details and not details.endswith("."):
        details += "."
    return summary, details


def _data_mode(tool_results: list[dict[str, Any]]) -> str | None:
    def source_modes(value: Any) -> set[str]:
        modes: set[str] = set()
        if isinstance(value, dict):
            for item in value.values():
                modes.update(source_modes(item))
        elif isinstance(value, list):
            for item in value:
                modes.update(source_modes(item))
        elif isinstance(value, str):
            lowered = value.lower()
            if "simulator" in lowered:
                modes.add("simulator")
            elif any(token in lowered for token in ("open_meteo", "realtime", "real_time", "live")):
                modes.add("realtime")
        return modes

    modes = set().union(*(source_modes(result.get("data")) for result in tool_results))
    if "simulator" in modes:
        return "simulator"
    return "realtime" if "realtime" in modes else None


def _quality_status(intent: Intent, outcome: str, tool_results: list[dict[str, Any]]) -> str | None:
    environmental_intents = {
        Intent.CURRENT,
        Intent.COMPARE,
        Intent.HISTORY,
        Intent.FORECAST,
        Intent.ALERT,
        Intent.WEATHER,
        Intent.RECOMMENDATION,
        Intent.PROPOSAL,
        Intent.IMPACT,
        Intent.SPATIAL,
    }
    if intent not in environmental_intents:
        return None
    if outcome == "answered":
        return "fresh"
    if outcome != "insufficient_data":
        return None
    for result in tool_results:
        data = result.get("data") or {}
        status = str(data.get("status") or "").lower()
        if status in {"stale", "offline", "invalid"}:
            return status
        if data.get("is_stale") is True:
            return "stale"
    return None


def _failure_reason(outcome: str, tool_results: list[dict[str, Any]]) -> str | None:
    if outcome != "insufficient_data":
        return None
    for result in tool_results:
        if not result.get("ok", False):
            code = str(result.get("code") or "backend_unavailable")
            return "timeout" if "timeout" in code else code
        data = result.get("data") or {}
        status = str(data.get("status") or "").lower()
        if status in {"stale", "offline", "invalid"}:
            return f"{status}_data"
        if data.get("is_stale") is True:
            return "stale_data"
    return "missing_or_invalid_evidence"


async def generate_explanation_node(state: AgentState) -> dict[str, Any]:
    """Record the deterministic generation mode without calling a provider.

    The response composer already owns the complete grounded answer. Provider-backed
    semantic routing is observed separately and never misreported as live generation.
    """
    route = state.get("route")
    observation = state.get("llm_observation") or {"llm_call_count": 0}
    generation: dict[str, Any] = {
        "generation_mode": "deterministic_grounded",
        "llm_call_count": int(observation.get("llm_call_count", 0)),
    }
    if isinstance(route, dict) and route.get("conversation_kind"):
        generation["conversation_mode"] = "deterministic_social"
    if generation["llm_call_count"]:
        generation.update(
            {
                key: value
                for key, value in observation.items()
                if key
                in {
                    "llm_stage",
                    "provider",
                    "model",
                    "llm_latency_ms",
                    "token_usage",
                    "semantic_router_outcome",
                    "failure_code",
                }
                and value is not None
            }
        )
    return {"generation": generation}


def trace_node(state: AgentState) -> dict[str, Any]:
    decision = RouteDecision.model_validate(state["route"])
    trace = {
        "request_id": state["request_id"],
        "intent": decision.intent.value,
        "conversation_kind": decision.conversation_kind,
        "policy_version": GROUNDING_POLICY_VERSION,
        "tools": state.get("tool_traces", []),
        "safety_category": decision.safety_category.value if decision.safety_category else None,
        "refusal_category": decision.refusal_category.value if decision.refusal_category else None,
        "reason_code": decision.reason_code.value if decision.reason_code else None,
        "routing_mode": decision.routing_mode,
        "semantic_confidence": decision.semantic_confidence,
        "final_outcome": state.get("outcome", "unknown"),
        "latency_ms": round((perf_counter() - state["started_at"]) * 1000, 3),
        **state.get("generation", {"generation_mode": "deterministic_grounded"}),
    }
    if decision.intent == Intent.RECOMMENDATION:
        trace["recommendation_policy_version"] = RECOMMENDATION_POLICY_VERSION
    if decision.intent == Intent.IMPACT:
        trace["impact_policy_version"] = IMPACT_POLICY_VERSION
    if decision.intent == Intent.PROPOSAL and decision.safety_category is None:
        trace["proposal_policy_version"] = PROPOSAL_POLICY_VERSION
    emit_trace(trace)
    return {"trace": trace}
