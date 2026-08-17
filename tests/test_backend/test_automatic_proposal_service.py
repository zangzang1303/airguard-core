from __future__ import annotations

from datetime import UTC, datetime

from backend.app.services.automatic_proposal_service import AutomaticProposalService


class FakeAgentService:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def chat_sync(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeApprovalService:
    def __init__(self, exists: bool = False, pending: bool = False) -> None:
        self.exists = exists
        self.pending = pending

    def has_request_for_alert(self, **_kwargs) -> bool:
        return self.exists

    def has_pending_warning_proposal(self, **_kwargs) -> bool:
        return self.pending

    def expire_pending_requests(self, **_kwargs) -> int:
        return 0


class FakeAuditService:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(self, **kwargs):
        self.records.append(kwargs)
        return {"audit_id": 1}


def alert(**overrides):
    result = {
        "alert_id": "alert-001",
        "station_id": "S02",
        "alert_type": "aqi_threshold",
        "status": "active",
        "created_at": datetime(2026, 8, 15, tzinfo=UTC),
    }
    result.update(overrides)
    return result


def test_auto_proposal_requires_new_active_environmental_alert() -> None:
    service = AutomaticProposalService(
        agent_service=FakeAgentService([]), approval_service=FakeApprovalService(), audit_service=FakeAuditService(), enabled=True
    )

    assert service.should_analyze(alert()) is True
    assert service.should_analyze(alert(alert_type="sensor_offline")) is False
    assert service.should_analyze(alert(status="resolved")) is False
    assert service.should_analyze(None) is False


def test_auto_proposal_allows_only_one_pending_or_scheduled_proposal_per_station() -> None:
    service = AutomaticProposalService(
        agent_service=FakeAgentService([]), approval_service=FakeApprovalService(), audit_service=FakeAuditService(), enabled=True
    )

    assert service.should_analyze(alert()) is True
    assert service.should_analyze(alert()) is False

    blocked = AutomaticProposalService(
        agent_service=FakeAgentService([]), approval_service=FakeApprovalService(pending=True), audit_service=FakeAuditService(), enabled=True
    )
    assert blocked.should_analyze(alert()) is False


def test_auto_proposal_station_allowlist_can_focus_demo_on_s05() -> None:
    service = AutomaticProposalService(
        agent_service=FakeAgentService([]), approval_service=FakeApprovalService(), audit_service=FakeAuditService(),
        enabled=True, allowed_stations=("S05",),
    )

    assert service.should_analyze(alert(station_id="S05")) is True
    assert service.should_analyze(alert(station_id="S03")) is False


def test_auto_proposal_uses_live_llm_before_creating_pending_proposal() -> None:
    agent = FakeAgentService([
        {"trace": {"generation_mode": "live_llm", "final_outcome": "answered"}},
        {"proposal_id": "proposal-001", "trace": {"final_outcome": "proposal_pending"}},
    ])
    audit = FakeAuditService()
    service = AutomaticProposalService(
        agent_service=agent, approval_service=FakeApprovalService(), audit_service=audit, enabled=True
    )

    service.analyze_and_propose(alert=alert(), correlation_id="corr-001")

    assert len(agent.calls) == 2
    assert agent.calls[0]["station_id"] == "S02"
    assert "Danh gia" in agent.calls[0]["message"]
    assert "warning proposal" in agent.calls[1]["message"]
    assert audit.records[-1]["action"] == "agent.auto_proposal.create"
    assert audit.records[-1]["details"]["proposal_id"] == "proposal-001"


def test_auto_proposal_does_not_create_when_live_llm_is_unavailable() -> None:
    agent = FakeAgentService([{"trace": {"generation_mode": "deterministic_grounded"}}])
    audit = FakeAuditService()
    service = AutomaticProposalService(
        agent_service=agent, approval_service=FakeApprovalService(), audit_service=audit, enabled=True
    )

    service.analyze_and_propose(alert=alert(), correlation_id="corr-002")

    assert len(agent.calls) == 1
    assert audit.records[-1]["action"] == "agent.auto_proposal.skipped"
    assert audit.records[-1]["outcome"] == "skipped"
