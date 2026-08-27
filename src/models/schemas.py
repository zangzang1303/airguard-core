from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ConversationContext(BaseModel):
    """Backend-validated semantic memory; never contains prior facts or prose."""

    model_config = ConfigDict(extra="forbid")

    context_version: int = Field(default=1, ge=1, le=1)
    station_ids: list[str] = Field(default_factory=list, max_length=5)
    primary_station_id: str | None = None
    last_intent: str | None = Field(default=None, max_length=40)
    turn_count: int = Field(default=0, ge=0)

    @field_validator("station_ids")
    @classmethod
    def validate_station_ids(cls, values: list[str]) -> list[str]:
        normalized = [value.upper() for value in values]
        if any(value not in {"S01", "S02", "S03", "S04", "S05"} for value in normalized):
            raise ValueError("conversation station_ids must be limited to S01-S05")
        if len(set(normalized)) != len(normalized):
            raise ValueError("conversation station_ids must be unique")
        return normalized

    @field_validator("primary_station_id")
    @classmethod
    def validate_primary_station_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.upper()
        if normalized not in {"S01", "S02", "S03", "S04", "S05"}:
            raise ValueError("primary_station_id must be limited to S01-S05")
        return normalized

    @field_validator("last_intent")
    @classmethod
    def validate_last_intent(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in {
            "current",
            "compare",
            "history",
            "forecast",
            "active_alerts",
            "weather",
            "recommendation",
            "proposal",
            "impact",
            "spatial",
        }:
            raise ValueError("last_intent is not allow-listed")
        return value

    @model_validator(mode="after")
    def primary_belongs_to_station_ids(self) -> ConversationContext:
        if self.primary_station_id and self.primary_station_id not in self.station_ids:
            raise ValueError("primary_station_id must be present in station_ids")
        return self


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
    conversation_context: ConversationContext | None = Field(
        default=None,
        description="Bounded semantic context supplied by the backend system of record",
    )


class AgentSource(BaseModel):
    tool_name: str
    station_id: str | None = None
    observed_at: str | None = None
    source: str | None = None


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded final answer")
    answer_summary: str | None = Field(default=None, description="Concise grounded answer summary")
    answer_details: str | None = Field(default=None, description="Grounded evidence and limitations")
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
    data_mode: str | None = None
    quality: str | None = None
    failure_reason: str | None = None
    clarification: str | None = None
    pending: bool = False
    refusal_category: str | None = None
    reason_code: str | None = None
    trace: dict[str, Any] = Field(default_factory=dict)
    # Compatibility fields for the original template client.
    response: str = Field(default="", description="Deprecated alias of answer")
    analysis: str = Field(default="", description="Non-sensitive routing summary")
