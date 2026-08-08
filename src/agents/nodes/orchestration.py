from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import uuid4

from src.agents.policies.grounding import GROUNDING_POLICY_VERSION, Intent, RouteDecision, route_query
from src.agents.policies.recommendations import RECOMMENDATION_POLICY_VERSION
from src.agents.response_composer import compose_response
from src.agents.state import AgentState
from src.agents.tools.contracts import ToolError, ToolErrorCode
from src.agents.trace import emit_trace


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
    composed = compose_response(decision, state.get("tool_results", []))
    result = {
        "answer": composed["answer"],
        "response": composed["answer"],
        "sources": composed["sources"],
        "outcome": composed["outcome"],
    }
    if composed.get("recommendation_policy_version"):
        result["recommendation_policy_version"] = composed["recommendation_policy_version"]
    return result


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
    }
    if decision.intent == Intent.RECOMMENDATION:
        trace["recommendation_policy_version"] = RECOMMENDATION_POLICY_VERSION
    emit_trace(trace)
    return {"trace": trace}
