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
        self.created: list[dict] = []

    def has_request_for_alert(self, **_kwargs) -> bool:
        return self.exists

    def has_pending_warning_proposal(self, **_kwargs) -> bool:
        return self.pending

    def expire_pending_requests(self, **_kwargs) -> int:
        return 0

    def create_request(self, **kwargs) -> dict:
        self.created.append(kwargs)
        return {"request_id": "eco-proposal-001", "status": "pending"}


class FakeAuditService:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(self, **kwargs):
        self.records.append(kwargs)
        return {"audit_id": 1}


class FakeNotifier:
    def __init__(self, *, failure: Exception | None = None) -> None:
        self.failure = failure
        self.calls: list[dict] = []

    def __call__(self, **kwargs) -> None:
        self.calls.append(kwargs)
        if self.failure:
            raise self.failure


def alert(**overrides):
    result = {
        "alert_id": "alert-001",
        "station_id": "S02",
        "alert_type": "pm25_threshold",
        "status": "active",
        "created_at": datetime(2026, 8, 15, tzinfo=UTC),
        "ventilation_eligible": True,
    }
    result.update(overrides)
    return result


def test_auto_proposal_requires_new_active_environmental_alert() -> None:
    service = AutomaticProposalService(
        agent_service=FakeAgentService([]), approval_service=FakeApprovalService(), audit_service=FakeAuditService(), enabled=True
    )

    assert service.should_analyze(alert()) is True
    assert service.should_analyze(alert(alert_type="sensor_offline")) is False
    assert service.should_analyze(alert(alert_type="aqi_threshold")) is False
    assert service.should_analyze(alert(ventilation_eligible=False)) is False
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
    notifier = FakeNotifier()
    service = AutomaticProposalService(
        agent_service=agent,
        approval_service=FakeApprovalService(),
        audit_service=audit,
        enabled=True,
        proposal_notifier=notifier,
    )

    service.analyze_and_propose(alert=alert(), correlation_id="corr-001")

    assert len(agent.calls) == 2
    assert agent.calls[0]["station_id"] == "S02"
    assert "Danh gia" in agent.calls[0]["message"]
    assert "warning proposal" in agent.calls[1]["message"]
    assert audit.records[-1]["action"] == "agent.auto_proposal.create"
    assert audit.records[-1]["details"]["proposal_id"] == "proposal-001"
    assert audit.records[-1]["details"]["station_id"] == "S02"
    assert notifier.calls == [
        {
            "proposal_id": "proposal-001",
            "station_id": "S02",
            "proposed_action": "ventilation_boost",
            "correlation_id": "corr-001",
        }
    ]


def test_auto_proposal_uses_grounded_deterministic_fallback_when_live_llm_is_unavailable() -> None:
    agent = FakeAgentService([{"trace": {"generation_mode": "deterministic_grounded"}}])
    audit = FakeAuditService()
    approvals = FakeApprovalService()
    notifier = FakeNotifier()
    service = AutomaticProposalService(
        agent_service=agent,
        approval_service=approvals,
        audit_service=audit,
        enabled=True,
        proposal_notifier=notifier,
    )

    service.analyze_and_propose(alert=alert(), correlation_id="corr-002")

    assert len(agent.calls) == 1
    assert approvals.created[0]["proposed_action"] == "ventilation_boost"
    assert approvals.created[0]["created_by"] == "ai_agent"
    assert approvals.created[0]["evidence"]["automation"]["generation_mode"] == "deterministic_grounded"
    assert audit.records[-1]["action"] == "agent.auto_proposal.create"
    assert audit.records[-1]["details"]["generation_mode"] == "deterministic_grounded"
    assert audit.records[-1]["details"]["station_id"] == "S02"
    assert notifier.calls[0]["proposal_id"] == "eco-proposal-001"


def test_auto_proposal_rejects_ungrounded_generation_mode() -> None:
    agent = FakeAgentService([{"trace": {"generation_mode": "unknown"}}])
    audit = FakeAuditService()
    approvals = FakeApprovalService()
    service = AutomaticProposalService(
        agent_service=agent,
        approval_service=approvals,
        audit_service=audit,
        enabled=True,
    )

    service.analyze_and_propose(alert=alert(), correlation_id="corr-ungrounded")

    assert approvals.created == []
    assert audit.records[-1]["action"] == "agent.auto_proposal.skipped"
    assert audit.records[-1]["details"]["reason"] == "grounded_generation_required"


def test_safe_recovery_creates_pending_eco_proposal_without_agent_or_dispatch() -> None:
    approvals = FakeApprovalService()
    agent = FakeAgentService([])
    notifier = FakeNotifier()
    audit = FakeAuditService()
    service = AutomaticProposalService(
        agent_service=agent,
        approval_service=approvals,
        audit_service=audit,
        enabled=True,
        proposal_notifier=notifier,
    )
    recovery = alert(
        alert_id="eco-recovery:intent-1",
        alert_type="ventilation_recovery",
        ventilation_eligible=False,
        ventilation_recovery_eligible=True,
        device_id="FILTER-01",
        ventilation_evidence={
            "source_command_intent_id": "intent-1",
            "policy_version": "ventilation-recovery-v1",
        },
    )

    assert service.should_analyze(recovery) is True
    service.analyze_and_propose(alert=recovery, correlation_id="corr-recovery")

    assert agent.calls == []
    assert approvals.created[0]["proposed_action"] == "eco_mode"
    assert approvals.created[0]["idempotency_key"] == "eco-recovery:intent-1:v1"
    assert audit.records[-1]["details"]["station_id"] == "S02"
    assert notifier.calls[0]["proposed_action"] == "eco_mode"


def test_notification_failure_is_audited_without_losing_persisted_proposal() -> None:
    agent = FakeAgentService(
        [
            {"trace": {"generation_mode": "live_llm", "final_outcome": "answered"}},
            {"proposal_id": "proposal-notify-001", "trace": {"final_outcome": "proposal_pending"}},
        ]
    )
    audit = FakeAuditService()
    notifier = FakeNotifier(failure=ConnectionError("notification broker unavailable"))
    service = AutomaticProposalService(
        agent_service=agent,
        approval_service=FakeApprovalService(),
        audit_service=audit,
        enabled=True,
        proposal_notifier=notifier,
    )

    service.analyze_and_propose(alert=alert(), correlation_id="corr-notify-failure")

    assert notifier.calls[0]["proposal_id"] == "proposal-notify-001"
    assert audit.records[-1]["action"] == "proposal.notification.failure"
    assert audit.records[-1]["outcome"] == "failure"
