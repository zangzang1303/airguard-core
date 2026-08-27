from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Literal

from src.agents.tools.contracts import ProposalEvidence, ToolName

PROPOSAL_POLICY_VERSION = "2026-08-08.ai-005"


@dataclass(frozen=True)
class ProposalEligibilityDecision:
    eligible: bool
    reason_code: str
    evidence: tuple[ProposalEvidence, ...] = ()
    alert_id: str | None = None
    proposed_action: str = "notify_station_area_users"
    duration_minutes: int | None = None
    intensity_percent: int | None = None


def evaluate_proposal_eligibility(
    station_id: str,
    current: Mapping[str, Any],
    alerts: list[Mapping[str, Any]],
) -> ProposalEligibilityDecision:
    status = str(current.get("status", "")).lower()
    if status != "online":
        return ProposalEligibilityDecision(False, f"station_{status or 'invalid'}")
    if current.get("is_stale") is not False:
        return ProposalEligibilityDecision(False, "measurement_stale")
    if current.get("pm25") is None or not current.get("source") or not current.get("updated_at"):
        return ProposalEligibilityDecision(False, "measurement_invalid")

    active_alerts = [
        item
        for item in alerts
        if item.get("station_id") == station_id and item.get("status") == "active"
    ]
    alert = next(
        (
            item for item in active_alerts
            if item.get("alert_type") in {"pm25_threshold", "co2_threshold"}
            and item.get("ventilation_eligible") is True
        ),
        active_alerts[0] if active_alerts else None,
    )
    if alert is None:
        return ProposalEligibilityDecision(False, "active_alert_required")
    if not alert.get("alert_id") or not alert.get("source") or not alert.get("created_at"):
        return ProposalEligibilityDecision(False, "alert_evidence_invalid")

    evidence = (
        ProposalEvidence(
            source_tool=ToolName.GET_CURRENT_PM25,
            station_id=station_id,
            aqi=current.get("aqi"),
            aqi_category=current.get("aqi_category"),
            pm25=current.get("pm25"),
            co2=current.get("co2"),
            noise_db=current.get("noise_db"),
            temperature=current.get("temperature"),
            observed_value=current["pm25"],
            measured_at=current["updated_at"],
            source=current["source"],
        ),
        ProposalEvidence(
            source_tool=ToolName.GET_ACTIVE_ALERTS,
            evidence_id=str(alert["alert_id"]),
            station_id=station_id,
            observed_value=alert.get("observed_value"),
            threshold_value=alert.get("threshold_value"),
            measured_at=alert["created_at"],
            source=alert["source"],
            rule_version=alert.get("rule_version"),
            severity=alert.get("severity"),
            alert_type=alert.get("alert_type"),
            ventilation_eligible=alert.get("ventilation_eligible"),
            ventilation_policy_version=alert.get("ventilation_policy_version"),
            qualified_duration_seconds=alert.get("qualified_duration_seconds"),
            qualification_window_start=alert.get("qualification_window_start"),
            qualification_window_end=alert.get("qualification_window_end"),
            triggered_metrics=alert.get("triggered_metrics") or [],
        ),
    )
    is_ventilation = (
        alert.get("alert_type") in {"pm25_threshold", "co2_threshold"}
        and alert.get("ventilation_eligible") is True
    )
    duration_minutes = int(alert.get("recommended_duration_minutes") or 45) if is_ventilation else None
    intensity_percent = int(alert.get("recommended_intensity_percent") or 80) if is_ventilation else None
    return ProposalEligibilityDecision(
        True,
        "eligible",
        evidence=evidence,
        alert_id=str(alert["alert_id"]),
        proposed_action="ventilation_boost" if is_ventilation else "notify_station_area_users",
        duration_minutes=duration_minutes,
        intensity_percent=intensity_percent,
    )


def proposal_idempotency_key(
    station_id: str,
    alert_id: str,
    policy_version: str = PROPOSAL_POLICY_VERSION,
) -> str:
    material = f"{station_id}:{alert_id}:{policy_version}".encode()
    return f"agent-proposal-{sha256(material).hexdigest()[:32]}"


def proposal_action(
    decision: ProposalEligibilityDecision | None = None,
) -> Literal["notify_station_area_users", "ventilation_boost"]:
    return decision.proposed_action if decision else "notify_station_area_users"
