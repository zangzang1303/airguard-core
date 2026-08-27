from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request

from src.agents.graph import agent
from src.agents.metrics import snapshot
from src.agents.policies.grounding import GROUNDING_POLICY_VERSION
from src.models.schemas import ChatRequest, ChatResponse

router = APIRouter()
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")


async def _chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    request_id = http_request.headers.get("X-Request-ID")
    initial_state = {
        "query": request.message,
        "user_id": request.user_id,
        "context_station_id": request.station_id,
        "conversation_context": (
            request.conversation_context.model_dump(mode="json")
            if request.conversation_context
            else {}
        ),
    }
    if request_id and REQUEST_ID_PATTERN.fullmatch(request_id):
        initial_state["request_id"] = request_id
    try:
        result = await agent.ainvoke(initial_state)
        route = result.get("route", {})
        return ChatResponse(
            answer=result["answer"],
            answer_summary=result.get("answer_summary"),
            answer_details=result.get("answer_details"),
            intent=route.get("intent", "out_of_scope"),
            conversation_kind=route.get("conversation_kind"),
            response=result["answer"],
            analysis=result.get("analysis", ""),
            used_tools=result.get("used_tools", []),
            tool_arguments=route.get("tool_arguments", []),
            sources=result.get("sources", []),
            map_actions=[],
            request_id=result["request_id"],
            proposal_id=result.get("proposal_id"),
            recommendation_policy_version=result.get("recommendation_policy_version"),
            impact_policy_version=result.get("impact_policy_version"),
            outcome=result.get("outcome", "unknown"),
            data_mode=result.get("data_mode"),
            quality=result.get("quality"),
            failure_reason=result.get("failure_reason"),
            clarification=result.get("clarification"),
            pending=result.get("pending", False),
            refusal_category=route.get("refusal_category"),
            reason_code=route.get("reason_code"),
            trace=result.get("trace", {}),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Agent request failed safely.") from exc


@router.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    return await _chat(request, http_request)


@router.post("/chat", response_model=ChatResponse, deprecated=True)
async def legacy_chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    return await _chat(request, http_request)


@router.get("/status")
async def agent_status() -> dict[str, str]:
    return {
        "status": "ready",
        "agent": "AirGuard grounded Agent",
        "policy_version": GROUNDING_POLICY_VERSION,
    }


@router.get("/metrics")
async def agent_metrics() -> dict:
    """Return bounded aggregate metrics without prompts, user IDs or sources."""
    return snapshot()
