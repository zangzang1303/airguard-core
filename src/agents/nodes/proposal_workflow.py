from __future__ import annotations

from time import perf_counter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.agents.policies.proposal_eligibility import (
    PROPOSAL_POLICY_VERSION,
    evaluate_proposal_eligibility,
    proposal_action,
    proposal_idempotency_key,
)
from src.agents.tools.contracts import (
    CurrentPm25Input,
    ToolEnvelope,
    ToolError,
    ToolErrorCode,
    ToolName,
    UserProfileInput,
)


class ProposalWorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["created", "blocked", "failed"]
    reason_code: str
    proposal_id: str | None = None
    status: Literal["pending"] | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    tool_traces: list[dict[str, Any]] = Field(default_factory=list)


async def run_proposal_workflow(
    station_id: str,
    user_id: str,
    request_id: str,
    tool_client: Any,
    *,
    bypass_requested: bool = False,
) -> ProposalWorkflowResult:
    if bypass_requested:
        return ProposalWorkflowResult(outcome="blocked", reason_code="hitl_bypass_refused")

    try:
        station_id = CurrentPm25Input(station_id=station_id).station_id
        user_id = UserProfileInput(user_id=user_id).user_id
        if not request_id.strip():
            raise ValueError("request_id is required")
    except (ValidationError, ValueError):
        return ProposalWorkflowResult(outcome="blocked", reason_code="invalid_input")

    tool_results: list[dict[str, Any]] = []
    tool_traces: list[dict[str, Any]] = []

    current = await _call_tool(
        tool_client,
        ToolName.GET_CURRENT_PM25,
        {"station_id": station_id},
        request_id,
        tool_results,
        tool_traces,
    )
    if isinstance(current, ToolError):
        return _result("failed", "current_tool_error", tool_results, tool_traces)

    alerts = await _call_tool(
        tool_client,
        ToolName.GET_ACTIVE_ALERTS,
        {"station_id": station_id},
        request_id,
        tool_results,
        tool_traces,
    )
    if isinstance(alerts, ToolError):
        return _result("failed", "alerts_tool_error", tool_results, tool_traces)

    decision = evaluate_proposal_eligibility(
        station_id,
        current.data,
        alerts.data.get("items", []),
    )
    evidence = [item.model_dump(mode="json") for item in decision.evidence]
    if not decision.eligible or decision.alert_id is None:
        return _result(
            "blocked",
            decision.reason_code,
            tool_results,
            tool_traces,
            evidence=evidence,
        )

    payload = {
        "user_id": user_id,
        "idempotency_key": proposal_idempotency_key(station_id, decision.alert_id),
        "target": {"audience": "station_area", "station_id": station_id},
        "action": proposal_action(),
        "rationale": (
            "Fresh simulator PM2.5 data and an active backend alert require manager review."
        ),
        "policy_version": PROPOSAL_POLICY_VERSION,
        "evidence": evidence,
    }
    created = await _call_tool(
        tool_client,
        ToolName.CREATE_WARNING_PROPOSAL,
        payload,
        request_id,
        tool_results,
        tool_traces,
    )
    if isinstance(created, ToolError):
        return _result(
            "failed",
            "proposal_create_failed",
            tool_results,
            tool_traces,
            evidence=evidence,
        )
    if created.data.get("status") != "pending" or not created.data.get("proposal_id"):
        return _result(
            "failed",
            "proposal_response_invalid",
            tool_results,
            tool_traces,
            evidence=evidence,
        )
    return ProposalWorkflowResult(
        outcome="created",
        reason_code="proposal_pending",
        proposal_id=created.data["proposal_id"],
        status="pending",
        evidence=evidence,
        tool_results=tool_results,
        tool_traces=tool_traces,
    )


async def _call_tool(
    tool_client: Any,
    tool_name: ToolName,
    payload: dict[str, Any],
    request_id: str,
    tool_results: list[dict[str, Any]],
    tool_traces: list[dict[str, Any]],
) -> ToolEnvelope | ToolError:
    started_at = perf_counter()
    try:
        method = getattr(tool_client, tool_name.value)
        result = await method(payload, request_id=request_id)
        if not isinstance(result, (ToolEnvelope, ToolError)):
            raise TypeError("tool adapter returned an unsupported result")
    except Exception as exc:
        result = ToolError(
            tool_name=tool_name,
            code=ToolErrorCode.UNAVAILABLE,
            message="Tool adapter failed safely.",
            request_id=request_id,
            details={"error_type": exc.__class__.__name__},
        )
    tool_results.append(result.model_dump(mode="json"))
    tool_traces.append(
        {
            "tool_name": tool_name.value,
            "status": "success" if result.ok else result.code.value,
            "latency_ms": round((perf_counter() - started_at) * 1000, 3),
        }
    )
    return result


def _result(
    outcome: Literal["blocked", "failed"],
    reason_code: str,
    tool_results: list[dict[str, Any]],
    tool_traces: list[dict[str, Any]],
    *,
    evidence: list[dict[str, Any]] | None = None,
) -> ProposalWorkflowResult:
    return ProposalWorkflowResult(
        outcome=outcome,
        reason_code=reason_code,
        evidence=evidence or [],
        tool_results=tool_results,
        tool_traces=tool_traces,
    )
