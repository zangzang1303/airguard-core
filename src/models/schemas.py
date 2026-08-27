from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ConversationTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    text: str = Field(..., min_length=1, max_length=1200)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    user_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        pattern=r"^[A-Za-z0-9_.:@-]+$",
        description="Backend user identifier used only for profile tool lookup",
    )
    station_id: str | None = Field(
        default=None,
        pattern=r"^S0[1-5]$",
        description="Optional station context selected in the dashboard",
    )
    conversation: list[ConversationTurn] = Field(
        default_factory=list,
        max_length=6,
        description="Most recent visible chat turns for bounded follow-up resolution",
    )


class AgentSource(BaseModel):
    tool_name: str
    station_id: str | None = None
    observed_at: str | None = None
    source: str | None = None


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded final answer")
    intent: str
    conversation_kind: str | None = None
    used_tools: list[str] = Field(default_factory=list)
    tool_arguments: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[AgentSource] = Field(default_factory=list)
    map_actions: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str
    proposal_id: str | None = None
    recommendation_policy_version: str | None = None
    impact_policy_version: str | None = None
    outcome: str = Field(default="unknown", description="Grounded request outcome")
    refusal_category: str | None = None
    reason_code: str | None = None
    trace: dict[str, Any] = Field(default_factory=dict)
    # Compatibility fields for the original template client.
    response: str = Field(default="", description="Deprecated alias of answer")
    analysis: str = Field(default="", description="Non-sensitive routing summary")
