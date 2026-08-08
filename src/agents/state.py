from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Serializable state passed through the grounded LangGraph workflow."""

    query: str
    user_id: str
    context_station_id: str
    request_id: str
    started_at: float
    route: dict[str, Any]
    tool_results: list[dict[str, Any]]
    tool_traces: list[dict[str, Any]]
    used_tools: list[str]
    sources: list[dict[str, Any]]
    answer: str
    response: str
    analysis: str
    outcome: str
    recommendation_policy_version: str
    trace: dict[str, Any]
