from __future__ import annotations

from threading import Lock
from typing import Any

from .agent_service import AgentService, AgentServiceError
from .approval_service import ApprovalService
from .audit_service import AuditService


class AutomaticProposalService:
    """Turns a backend-confirmed environmental alert into one Agent review request.

    The alert rule remains the eligibility gate. The Agent must first complete a
    live-LLM, tool-grounded analysis; only then may it create a pending proposal.
    """

    SYSTEM_USER_ID = "system-alert-agent"
    ELIGIBLE_ALERT_TYPES = {
        "pm25_threshold",
        "co2_threshold",
        "ventilation_recovery",
    }

    def __init__(
        self,
        *,
        agent_service: AgentService,
        approval_service: ApprovalService,
        audit_service: AuditService,
        enabled: bool,
        allowed_stations: tuple[str, ...] = (),
    ) -> None:
        self.agent_service = agent_service
        self.approval_service = approval_service
        self.audit_service = audit_service
        self.enabled = enabled
        self.allowed_stations = frozenset(allowed_stations)
        self._scheduled_stations: set[str] = set()
        self._schedule_lock = Lock()

    def should_analyze(self, alert: dict[str, Any] | None) -> bool:
        self.approval_service.expire_pending_requests()
        if not self.enabled or not alert or alert.get("status") != "active":
            return False
        alert_type = alert.get("alert_type")
        if alert_type not in self.ELIGIBLE_ALERT_TYPES:
            return False
        if alert_type == "ventilation_recovery":
            if alert.get("ventilation_recovery_eligible") is not True:
                return False
        elif alert.get("ventilation_eligible") is not True:
            return False
        station_id = alert.get("station_id")
        created_at = alert.get("created_at")
        if not station_id or not created_at:
            return False
        station_id = str(station_id)
        if self.allowed_stations and station_id.upper() not in self.allowed_stations:
            return False
        with self._schedule_lock:
            if station_id in self._scheduled_stations:
                return False
            if self.approval_service.has_pending_warning_proposal(station_id=station_id):
                return False
            if self.approval_service.has_request_for_alert(
                station_id=station_id, alert_created_at=created_at
            ):
                return False
            self._scheduled_stations.add(station_id)
            return True

    def analyze_and_propose(self, *, alert: dict[str, Any], correlation_id: str) -> None:
        """Run outside the ingestion response; failures are audited and never retried blindly."""
        station_id = str(alert["station_id"])
        alert_id = str(alert.get("alert_id") or "unknown")
        try:
            if self.approval_service.has_pending_warning_proposal(station_id=station_id):
                self._audit(
                    action="agent.auto_proposal.skipped",
                    alert_id=alert_id,
                    correlation_id=correlation_id,
                    outcome="skipped",
                    details={"reason": "pending_proposal_exists", "station_id": station_id},
                )
                return
            if alert.get("alert_type") == "ventilation_recovery":
                self._create_eco_recovery_proposal(
                    alert=alert,
                    alert_id=alert_id,
                    station_id=station_id,
                    correlation_id=correlation_id,
                )
                return
            analysis = self.agent_service.chat_sync(
                message=(
                    f"Danh gia grounded canh bao {alert_id} tai {station_id}; "
                    "chi xem xet de xuat thong gio khi backend xac nhan du 15 phut."
                ),
                user_id=self.SYSTEM_USER_ID,
                station_id=station_id,
                request_id=f"{correlation_id}:analysis",
            )
            generation_mode = analysis.get("trace", {}).get("generation_mode")
            if generation_mode != "live_llm":
                self._audit(
                    action="agent.auto_proposal.skipped",
                    alert_id=alert_id,
                    correlation_id=correlation_id,
                    outcome="skipped",
                    details={"reason": "live_llm_required", "generation_mode": generation_mode},
                )
                return

            proposal = self.agent_service.chat_sync(
                message=(
                    f"Tao warning proposal ventilation_boost pending cho {station_id} "
                    f"dua tren canh bao backend {alert_id}; khong phe duyet hoac dispatch."
                ),
                user_id=self.SYSTEM_USER_ID,
                station_id=station_id,
                request_id=f"{correlation_id}:proposal",
            )
            proposal_id = proposal.get("proposal_id")
            if not proposal_id:
                self._audit(
                    action="agent.auto_proposal.skipped",
                    alert_id=alert_id,
                    correlation_id=correlation_id,
                    outcome="skipped",
                    details={"reason": "proposal_not_created", "agent_outcome": proposal.get("trace", {}).get("final_outcome")},
                )
                return
            self._audit(
                action="agent.auto_proposal.create",
                alert_id=alert_id,
                correlation_id=correlation_id,
                details={"proposal_id": proposal_id, "generation_mode": generation_mode},
            )
        except AgentServiceError as exc:
            self._audit(
                action="agent.auto_proposal.failure",
                alert_id=alert_id,
                correlation_id=correlation_id,
                outcome="failure",
                details={"reason": exc.code},
            )
        except Exception as exc:
            self._audit(
                action="agent.auto_proposal.failure",
                alert_id=alert_id,
                correlation_id=correlation_id,
                outcome="failure",
                details={"reason": exc.__class__.__name__},
            )
        finally:
            with self._schedule_lock:
                self._scheduled_stations.discard(station_id)

    def _create_eco_recovery_proposal(
        self,
        *,
        alert: dict[str, Any],
        alert_id: str,
        station_id: str,
        correlation_id: str,
    ) -> None:
        evidence = dict(alert.get("ventilation_evidence") or {})
        source_intent_id = evidence.get("source_command_intent_id")
        if not source_intent_id:
            self._audit(
                action="agent.auto_proposal.skipped",
                alert_id=alert_id,
                correlation_id=correlation_id,
                outcome="skipped",
                details={"reason": "recovery_source_intent_missing", "station_id": station_id},
            )
            return
        evidence["control"] = {
            "action": "eco_mode",
            "duration_minutes": None,
            "intensity_percent": None,
            "policy_version": evidence.get("policy_version"),
        }
        proposal = self.approval_service.create_request(
            request_type="warning_proposal",
            station_id=station_id,
            device_id=alert.get("device_id"),
            proposed_action="eco_mode",
            reason="Fresh valid simulator data remained at safe PM2.5 and CO2 levels for 20 minutes; Manager review is required before eco mode.",
            evidence=evidence,
            created_by="system_ventilation_policy",
            correlation_id=correlation_id,
            idempotency_key=f"eco-recovery:{source_intent_id}:v1",
        )
        self._audit(
            action="agent.auto_proposal.create",
            alert_id=alert_id,
            correlation_id=correlation_id,
            details={
                "proposal_id": str(proposal["request_id"]),
                "proposed_action": "eco_mode",
                "source_command_intent_id": str(source_intent_id),
                "reused": bool(proposal.get("reused")),
            },
        )

    def _audit(
        self,
        *,
        action: str,
        alert_id: str,
        correlation_id: str,
        outcome: str = "success",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.audit_service.record(
            actor_type="agent",
            actor_id=self.SYSTEM_USER_ID,
            actor_role="agent",
            action=action,
            entity_type="alert",
            entity_id=alert_id,
            correlation_id=correlation_id,
            outcome=outcome,
            details=details,
        )
