from __future__ import annotations

from copy import deepcopy

import pytest

from src.agents.graph import build_graph
from src.agents.nodes.proposal_workflow import run_proposal_workflow
from src.agents.policies.proposal_eligibility import (
    PROPOSAL_POLICY_VERSION,
    proposal_idempotency_key,
)
from src.agents.tools.contracts import ToolError, ToolErrorCode, ToolName
from src.agents.tools.fake_adapter import DEFAULT_FIXTURES, FakeBackendToolClient


class ToolFailureAdapter(FakeBackendToolClient):
    def __init__(self, failed_tool: ToolName) -> None:
        super().__init__()
        self.failed_tool = failed_tool

    async def get_current_pm25(self, payload, request_id="fixture-request"):
        if self.failed_tool == ToolName.GET_CURRENT_PM25:
            return self._failure(ToolName.GET_CURRENT_PM25, request_id)
        return await super().get_current_pm25(payload, request_id)

    async def get_active_alerts(self, payload, request_id="fixture-request"):
        if self.failed_tool == ToolName.GET_ACTIVE_ALERTS:
            return self._failure(ToolName.GET_ACTIVE_ALERTS, request_id)
        return await super().get_active_alerts(payload, request_id)

    async def create_warning_proposal(self, payload, request_id="fixture-request"):
        if self.failed_tool == ToolName.CREATE_WARNING_PROPOSAL:
            return self._failure(ToolName.CREATE_WARNING_PROPOSAL, request_id)
        return await super().create_warning_proposal(payload, request_id)

    @staticmethod
    def _failure(tool_name: ToolName, request_id: str) -> ToolError:
        return ToolError(
            tool_name=tool_name,
            code=ToolErrorCode.UNAVAILABLE,
            message="fixture outage",
            request_id=request_id,
            status_code=503,
        )


@pytest.mark.asyncio
async def test_happy_path_creates_one_pending_proposal_with_complete_evidence():
    adapter = FakeBackendToolClient()

    result = await run_proposal_workflow("S02", "demo-user", "req-proposal", adapter)

    assert result.outcome == "created"
    assert result.reason_code == "proposal_pending"
    assert result.status == "pending"
    assert result.proposal_id == "proposal-001"
    assert len(adapter.created_proposals) == 1
    assert [item["source_tool"] for item in result.evidence] == [
        "get_current_pm25",
        "get_active_alerts",
    ]
    assert [trace["tool_name"] for trace in result.tool_traces] == [
        "get_current_pm25",
        "get_active_alerts",
        "create_warning_proposal",
    ]


@pytest.mark.asyncio
async def test_graph_routes_proposal_intent_to_pending_hitl_request():
    adapter = FakeBackendToolClient()

    result = await build_graph(adapter).ainvoke(
        {
            "query": "tao canh bao cho S02",
            "user_id": "demo-user",
            "context_station_id": "S02",
        }
    )

    assert result["proposal_id"] == "proposal-001"
    assert result["outcome"] == "proposal_pending"
    assert result["request_id"] == result["trace"]["request_id"]
    assert result["trace"]["proposal_policy_version"] == PROPOSAL_POLICY_VERSION
    assert "pending" in result["answer"]
    assert "Manager cần review" in result["answer"]
    assert result["used_tools"] == [
        "get_current_pm25",
        "get_active_alerts",
        "create_warning_proposal",
    ]


@pytest.mark.asyncio
async def test_graph_does_not_claim_success_when_create_tool_fails():
    result = await build_graph(ToolFailureAdapter(ToolName.CREATE_WARNING_PROPOSAL)).ainvoke(
        {
            "query": "tao canh bao cho S02",
            "user_id": "demo-user",
            "request_id": "req-create-failed",
        }
    )

    assert result.get("proposal_id") is None
    assert result["outcome"] == "failed"
    assert result["request_id"] == result["trace"]["request_id"] == "req-create-failed"
    assert "Không thể tạo warning proposal" in result["answer"]
    assert "Đã tạo warning proposal" not in result["answer"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "is_stale", "reason_code"),
    [
        ("offline", False, "station_offline"),
        ("online", True, "measurement_stale"),
        ("invalid", False, "station_invalid"),
    ],
)
async def test_bad_measurement_quality_blocks_create(status, is_stale, reason_code):
    current = deepcopy(DEFAULT_FIXTURES["current"])
    current["S02"].update({"status": status, "is_stale": is_stale})
    adapter = FakeBackendToolClient({"current": current})

    result = await run_proposal_workflow("S02", "demo-user", "req-quality", adapter)

    assert result.outcome == "blocked"
    assert result.reason_code == reason_code
    assert adapter.created_proposals == []


@pytest.mark.asyncio
async def test_missing_active_alert_blocks_create():
    adapter = FakeBackendToolClient()

    result = await run_proposal_workflow("S01", "demo-user", "req-no-alert", adapter)

    assert result.outcome == "blocked"
    assert result.reason_code == "active_alert_required"
    assert adapter.created_proposals == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failed_tool", "reason_code"),
    [
        (ToolName.GET_CURRENT_PM25, "current_tool_error"),
        (ToolName.GET_ACTIVE_ALERTS, "alerts_tool_error"),
        (ToolName.CREATE_WARNING_PROPOSAL, "proposal_create_failed"),
    ],
)
async def test_tool_failures_fail_closed_without_extra_create(failed_tool, reason_code):
    adapter = ToolFailureAdapter(failed_tool)

    result = await run_proposal_workflow("S02", "demo-user", "req-outage", adapter)

    assert result.outcome == "failed"
    assert result.reason_code == reason_code
    assert adapter.created_proposals == []


@pytest.mark.asyncio
async def test_bypass_request_is_refused_before_any_tool_call():
    adapter = FakeBackendToolClient()

    result = await run_proposal_workflow(
        "S02",
        "demo-user",
        "req-bypass",
        adapter,
        bypass_requested=True,
    )

    assert result.outcome == "blocked"
    assert result.reason_code == "hitl_bypass_refused"
    assert result.tool_traces == []
    assert adapter.created_proposals == []


@pytest.mark.asyncio
async def test_repeated_workflow_reuses_idempotent_proposal():
    adapter = FakeBackendToolClient()

    first = await run_proposal_workflow("S02", "demo-user", "req-first", adapter)
    second = await run_proposal_workflow("S02", "demo-user", "req-second", adapter)

    assert first.proposal_id == second.proposal_id == "proposal-001"
    assert len(adapter.created_proposals) == 1
    assert adapter.created_proposals[0]["idempotency_key"] == proposal_idempotency_key(
        "S02",
        "alert-S02-001",
    )


def test_idempotency_key_is_stable_for_alert_station_and_policy():
    first = proposal_idempotency_key("S02", "alert-S02-001", PROPOSAL_POLICY_VERSION)
    second = proposal_idempotency_key("S02", "alert-S02-001", PROPOSAL_POLICY_VERSION)
    changed = proposal_idempotency_key("S02", "alert-S02-002", PROPOSAL_POLICY_VERSION)

    assert first == second
    assert first != changed
    assert len(first) >= 8
