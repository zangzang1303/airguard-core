from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any
from uuid import uuid4

from src.agents.policies.grounding import GROUNDING_POLICY_VERSION, Intent, RouteDecision, route_query
from src.agents.policies.impact_assessment import IMPACT_POLICY_VERSION
from src.agents.policies.proposal_eligibility import PROPOSAL_POLICY_VERSION
from src.agents.policies.recommendations import RECOMMENDATION_POLICY_VERSION
from src.agents.response_composer import compose_response
from src.agents.state import AgentState
from src.agents.tools.contracts import ToolError, ToolErrorCode
from src.agents.trace import emit_trace
from src.config import get_settings
from src.services.llm import LlmProviderError, get_llm, resolve_llm_provider, resolved_model_name


def route_node(state: AgentState) -> dict[str, Any]:
    request_id = state.get("request_id") or f"agent-{uuid4()}"
    decision = route_query(
        state.get("query", ""),
        context_station_id=state.get("context_station_id"),
        user_id=state.get("user_id"),
        conversation=state.get("conversation", []),
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
    if decision.intent == Intent.PROPOSAL and decision.direct_response is None:
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
    route = state.get("route")
    # Social responses are fully deterministic by contract. Do not make an LLM
    # call even when a provider happens to be configured.
    if isinstance(route, dict) and route.get("conversation_kind"):
        return {"generation": {"generation_mode": "deterministic_grounded", "conversation_mode": "deterministic_social"}}

    settings = get_settings()
    base_answer = state.get("answer", "")
    fallback = {"generation_mode": "deterministic_grounded", "provider": None, "model": None}
    # The policy/composer owns every decision and fact in ``base_answer``. A
    # configured provider may only append a non-factual explanation, including
    # for transparent insufficient-data and safety-refusal outcomes. This lets
    # live eval cover those cases without delegating a quality gate or HITL
    # decision to the model.
    provider = resolve_llm_provider(settings)
    if provider is None:
        return {"generation": fallback}
    has_backend_evidence = bool(state.get("sources", []))
    started = perf_counter()
    try:
        llm = get_llm(settings=settings)
        prompt = (
            "Viết đúng một câu tiếng Việt ngắn, tối đa mười hai từ, chỉ nêu giới hạn dữ liệu "
            "hoặc ranh giới an toàn. Không thêm hay lặp số đo, thời gian, tên trạm, chỉ số, "
            "chẩn đoán, lệnh vận hành hoặc quyết định phê duyệt. "
            f"Outcome đã khóa: {state.get('outcome', 'unknown')}. "
            f"Evidence backend cùng request: {'present' if has_backend_evidence else 'none'}."
        )
        deadline_seconds = float(getattr(settings, "llm_response_deadline_seconds", 5.0))
        reply = await asyncio.wait_for(llm.ainvoke(prompt), timeout=deadline_seconds)
        explanation = str(reply.content).strip()
        # No numeric facts or station identifiers may come from the model-generated suffix.
        if not explanation or any(character.isdigit() for character in explanation) or "S0" in explanation.upper():
            raise ValueError("model output failed explanation safety validation")
        usage = getattr(reply, "usage_metadata", None) or {}
        return {
            "answer": f"{base_answer}\n\nGiải thích: {explanation}",
            "generation": {
                "generation_mode": "live_llm",
                "provider": provider,
                "model": resolved_model_name(settings, provider),
                "latency_ms": round((perf_counter() - started) * 1000, 3),
                "token_usage": dict(usage),
            },
        }
    except TimeoutError:
        return {
            "generation": {
                **fallback,
                "provider": provider,
                "model": resolved_model_name(settings, provider),
                "failure_code": "provider_deadline_exceeded",
                "latency_ms": round((perf_counter() - started) * 1000, 3),
            }
        }
    except Exception as exc:
        failure_code = str(exc) if isinstance(exc, LlmProviderError) else exc.__class__.__name__
        return {
            "generation": {
                **fallback,
                "provider": provider,
                "model": resolved_model_name(settings, provider),
                "failure_code": failure_code,
                "latency_ms": round((perf_counter() - started) * 1000, 3),
            }
        }


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
