from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, max_length=5000, description="User message")


class AgentSource(BaseModel):
    tool_name: str
    station_id: str | None = None
    observed_at: str | None = None
    source: str | None = None


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded final answer")
    used_tools: list[str] = Field(default_factory=list)
    sources: list[AgentSource] = Field(default_factory=list)
    request_id: str
    proposal_id: str | None = None
    trace: dict[str, Any] = Field(default_factory=dict)
    # Compatibility fields for the original template client.
    response: str = Field(default="", description="Deprecated alias of answer")
    analysis: str = Field(default="", description="Non-sensitive routing summary")
