from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request

from src.agents.graph import agent
from src.models.schemas import ChatRequest, ChatResponse

router = APIRouter()
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")


async def _chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    request_id = http_request.headers.get("X-Request-ID")
    initial_state = {
        "query": request.message,
        "user_id": request.user_id,
        "context_station_id": request.station_id,
    }
    if request_id and REQUEST_ID_PATTERN.fullmatch(request_id):
        initial_state["request_id"] = request_id
    try:
        result = await agent.ainvoke(initial_state)
        return ChatResponse(
            answer=result["answer"],
            response=result["answer"],
            analysis=result.get("analysis", ""),
            used_tools=result.get("used_tools", []),
            sources=result.get("sources", []),
            request_id=result["request_id"],
            recommendation_policy_version=result.get("recommendation_policy_version"),
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
    return {"status": "ready", "agent": "AirGuard grounded Agent", "policy_version": "2026-08-04.ai-002"}
