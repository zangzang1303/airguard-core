from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Serializable state passed through the grounded LangGraph workflow."""

    query: str
    user_id: str
    context_station_id: str
    conversation_context: dict[str, Any]
    request_id: str
    started_at: float
    route: dict[str, Any]
    tool_results: list[dict[str, Any]]
    tool_traces: list[dict[str, Any]]
    used_tools: list[str]
    sources: list[dict[str, Any]]
    answer: str
    answer_summary: str
    answer_details: str
    response: str
    analysis: str
    outcome: str
    intent: str
    data_mode: str | None
    quality: str | None
    failure_reason: str | None
    clarification: str | None
    pending: bool
    proposal_id: str | None
    proposal_reason_code: str | None
    recommendation_policy_version: str
    impact_policy_version: str
    generation: dict[str, Any]
    llm_observation: dict[str, Any]
    trace: dict[str, Any]
