from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import uuid4

from src.agents.policies.grounding import GROUNDING_POLICY_VERSION, Intent, RouteDecision, route_query
from src.agents.policies.proposal_eligibility import PROPOSAL_POLICY_VERSION
from src.agents.policies.impact_assessment import IMPACT_POLICY_VERSION
from src.agents.policies.recommendations import RECOMMENDATION_POLICY_VERSION
from src.agents.response_composer import compose_response
from src.agents.state import AgentState
from src.agents.tools.contracts import ToolError, ToolErrorCode
from src.agents.trace import emit_trace
from src.config import get_settings
from src.services.llm import get_llm


def route_node(state: AgentState) -> dict[str, Any]:
    request_id = state.get("request_id") or f"agent-{uuid4()}"
    decision = route_query(
        state.get("query", ""),
        context_station_id=state.get("context_station_id"),
        user_id=state.get("user_id"),
    )
    return {
        "request_id": request_id,
        "started_at": perf_counter(),
        "route": decision.model_dump(mode="json"),
        "analysis": f"intent={decision.intent.value}",
        "tool_results": [],
        "tool_traces": [],
        "used_tools": [],
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

    for tool_name, arguments in zip(decision.tool_calls, decision.tool_arguments, strict=True):
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

    return {"tool_results": results, "tool_traces": traces, "used_tools": used_tools}


def compose_node(state: AgentState) -> dict[str, Any]:
    decision = RouteDecision.model_validate(state["route"])
<<<<<<< HEAD
    if decision.direct_response is not None:
        composed = compose_response(decision, [])
        return {
            "answer": composed["answer"],
            "response": composed["answer"],
            "sources": composed["sources"],
            "outcome": composed["outcome"],
        }
    if decision.intent == Intent.PROPOSAL:
=======
    if decision.intent == Intent.PROPOSAL and decision.direct_response is None:
>>>>>>> dd46d3fc9426e86d81a4c06d467e970fce937fb6
        outcome = state.get("outcome")
        reason = state.get("proposal_reason_code")
        proposal_id = state.get("proposal_id")
        if outcome == "created" and proposal_id:
            return {
                "answer": (
                    f"Đã tạo warning proposal {proposal_id} ở trạng thái pending. "
                    "Manager cần review trước khi có bất kỳ lệnh thiết bị nào được dispatch."
                ),
                "response": f"Proposal {proposal_id} is pending manager review.",
                "sources": [],
                "outcome": "proposal_pending",
                "proposal_id": proposal_id,
            }
        return {
            "answer": f"Không thể tạo warning proposal: {reason or 'insufficient_evidence'}.",
            "response": f"Warning proposal blocked: {reason or 'insufficient_evidence'}.",
            "sources": [],
            "outcome": outcome or "blocked",
        }
    composed = compose_response(decision, state.get("tool_results", []))
    result = {
        "answer": composed["answer"],
        "response": composed["answer"],
        "sources": composed["sources"],
        "outcome": composed["outcome"],
    }
    if composed.get("recommendation_policy_version"):
        result["recommendation_policy_version"] = composed["recommendation_policy_version"]
    if decision.intent == Intent.IMPACT:
        result["impact_policy_version"] = IMPACT_POLICY_VERSION
    return result


async def generate_explanation_node(state: AgentState) -> dict[str, Any]:
    """Use a live model only after deterministic grounding has accepted the evidence.

    The model is allowed to add a plain-language explanation but cannot replace the
    fact-bearing deterministic answer. Provider outages retain that answer and are
    explicitly traced as a fallback, never as a successful live generation.
    """
    settings = get_settings()
    base_answer = state.get("answer", "")
    fallback = {"generation_mode": "deterministic_grounded", "provider": None, "model": None}
    if not settings.openai_api_key or state.get("outcome") != "answered":
        return {"generation": fallback}
    evidence = state.get("sources", [])
    started = perf_counter()
    try:
        llm = get_llm()
        prompt = (
            "You explain an already-grounded environmental answer. Do not add, change, infer, "
            "or repeat any measurements, timestamps, station names, forecast values, thresholds, "
            "medical advice, or claims of certainty. Write one short Vietnamese sentence that only "
            "explains how to interpret the evidence limitation.\n"
            f"Grounded answer (immutable): {base_answer}\n"
            f"Evidence references: {evidence}\n"
            "Return only the one explanatory sentence."
        )
        reply = await llm.ainvoke(prompt)
        explanation = str(reply.content).strip()
        # No numeric facts or station identifiers may come from the model-generated suffix.
        if not explanation or any(character.isdigit() for character in explanation) or "S0" in explanation.upper():
            raise ValueError("model output failed explanation safety validation")
        usage = getattr(reply, "usage_metadata", None) or {}
        return {
            "answer": f"{base_answer}\n\nGiải thích: {explanation}",
            "generation": {
                "generation_mode": "live_llm",
                "provider": "openai",
                "model": settings.model_name,
                "latency_ms": round((perf_counter() - started) * 1000, 3),
                "token_usage": dict(usage),
            },
        }
    except Exception as exc:
        return {"generation": {**fallback, "failure_code": exc.__class__.__name__, "latency_ms": round((perf_counter() - started) * 1000, 3)}}


def trace_node(state: AgentState) -> dict[str, Any]:
    decision = RouteDecision.model_validate(state["route"])
    trace = {
        "request_id": state["request_id"],
        "intent": decision.intent.value,
        "policy_version": GROUNDING_POLICY_VERSION,
        "tools": state.get("tool_traces", []),
        "safety_category": decision.safety_category.value if decision.safety_category else None,
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
