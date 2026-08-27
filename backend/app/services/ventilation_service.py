from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from .database import Database, dict_cursor

VENTILATION_POLICY_VERSION = "ventilation-continuity-v1"
ECO_RECOVERY_POLICY_VERSION = "ventilation-recovery-v1"
TIMED_DEVICE_ACTIONS = frozenset({"ventilation_boost", "air_purifier_on"})
ALLOWED_DEVICE_ACTIONS = frozenset({*TIMED_DEVICE_ACTIONS, "eco_mode"})


@dataclass(frozen=True)
class VentilationAssessment:
    eligible: bool
    reason_code: str
    policy_version: str
    required_duration_seconds: int
    continuous_duration_seconds: int = 0
    window_start: datetime | None = None
    window_end: datetime | None = None
    triggered_metrics: tuple[str, ...] = ()
    source_command_intent_id: str | None = None
    device_id: str | None = None
    evidence_source: str = "measurements"

    def as_evidence(self) -> dict[str, Any]:
        evidence = asdict(self)
        for field_name in ("window_start", "window_end"):
            value = evidence[field_name]
            evidence[field_name] = value.isoformat() if value else None
        evidence["triggered_metrics"] = list(self.triggered_metrics)
        return evidence


class VentilationService:
    """Rule-owned continuity checks for ventilation and recovery proposals.

    Only accepted measurements are stored as ``quality_flag='valid'``.  A
    missing/invalid sample therefore manifests as a gap, which must remain
    below ``max_gap_seconds`` for the continuous window to qualify.
    """

    def __init__(
        self,
        db: Database,
        *,
        pm25_threshold: float = 50.0,
        co2_threshold: float = 1000.0,
        trigger_duration_seconds: int = 15 * 60,
        recovery_duration_seconds: int = 20 * 60,
        stale_after_seconds: int = 300,
        max_gap_seconds: int = 60,
        default_duration_minutes: int = 45,
        default_intensity_percent: int = 80,
        demo_override_provider: Callable[[str], dict[str, Any] | None] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.db = db
        self.pm25_threshold = float(pm25_threshold)
        self.co2_threshold = float(co2_threshold)
        self.trigger_duration_seconds = max(1, int(trigger_duration_seconds))
        self.recovery_duration_seconds = max(1, int(recovery_duration_seconds))
        self.stale_after_seconds = max(1, int(stale_after_seconds))
        self.max_gap_seconds = max(1, min(int(max_gap_seconds), self.stale_after_seconds))
        if not 5 <= int(default_duration_minutes) <= 180:
            raise ValueError("default_duration_minutes must be between 5 and 180")
        if not 1 <= int(default_intensity_percent) <= 100:
            raise ValueError("default_intensity_percent must be between 1 and 100")
        self.default_duration_minutes = int(default_duration_minutes)
        self.default_intensity_percent = int(default_intensity_percent)
        self.demo_override_provider = demo_override_provider
        self._clock = clock or (lambda: datetime.now(UTC))

    def assess_trigger(
        self,
        station_id: str,
        *,
        reference_at: datetime | None = None,
    ) -> VentilationAssessment:
        reference_at = self._aware_utc(reference_at or self._clock())
        station_gate = self._station_status_gate(station_id)
        if station_gate:
            return VentilationAssessment(
                eligible=False,
                reason_code=station_gate,
                policy_version=VENTILATION_POLICY_VERSION,
                required_duration_seconds=self.trigger_duration_seconds,
            )
        demo_assessment = self._assess_demo_override(station_id, reference_at=reference_at)
        if demo_assessment is not None:
            return demo_assessment
        rows = self._measurements(
            station_id,
            reference_at=reference_at,
            required_seconds=self.trigger_duration_seconds,
        )
        assessment = self._assess_continuity(
            rows,
            reference_at=reference_at,
            required_seconds=self.trigger_duration_seconds,
            predicate=lambda row: self._is_trigger_measurement(row),
            policy_version=VENTILATION_POLICY_VERSION,
            failure_reason="threshold_not_continuous",
        )
        if not assessment.eligible:
            return assessment

        sequence = self._trailing_sequence(
            rows,
            reference_at=reference_at,
            predicate=self._is_trigger_measurement,
        )
        metrics: list[str] = []
        if sequence and all(float(row["pm25"]) > self.pm25_threshold for row in sequence):
            metrics.append("pm25")
        co2_values = [row.get("co2") for row in sequence]
        if co2_values and all(value is not None and float(value) > self.co2_threshold for value in co2_values):
            metrics.append("co2")
        if not metrics:
            # The OR condition was continuously true, even if the dominant
            # metric changed during the window. Keep that distinction explicit.
            metrics.append("pm25_or_co2")
        return VentilationAssessment(**{**asdict(assessment), "triggered_metrics": tuple(metrics)})

    def _assess_demo_override(
        self,
        station_id: str,
        *,
        reference_at: datetime,
    ) -> VentilationAssessment | None:
        if self.demo_override_provider is None:
            return None
        override = self.demo_override_provider(station_id)
        if not override:
            return None
        started_at_raw = override.get("started_at")
        if not isinstance(started_at_raw, datetime):
            return VentilationAssessment(
                False,
                "demo_override_timestamp_unavailable",
                VENTILATION_POLICY_VERSION,
                self.trigger_duration_seconds,
                evidence_source="demo_override",
            )
        started_at = self._aware_utc(started_at_raw)
        continuous_seconds = max(0, int((reference_at - started_at).total_seconds()))
        triggered_metrics: list[str] = []
        pm25 = override.get("pm25")
        co2 = override.get("co2")
        if pm25 is not None and float(pm25) > self.pm25_threshold:
            triggered_metrics.append("pm25")
        if co2 is not None and float(co2) > self.co2_threshold:
            triggered_metrics.append("co2")
        if not triggered_metrics:
            return VentilationAssessment(
                False,
                "threshold_not_continuous",
                VENTILATION_POLICY_VERSION,
                self.trigger_duration_seconds,
                continuous_seconds,
                started_at,
                reference_at,
                evidence_source="demo_override",
            )
        eligible = continuous_seconds >= self.trigger_duration_seconds
        return VentilationAssessment(
            eligible,
            "eligible" if eligible else "continuous_window_too_short",
            VENTILATION_POLICY_VERSION,
            self.trigger_duration_seconds,
            continuous_seconds,
            started_at,
            reference_at,
            tuple(triggered_metrics),
            evidence_source="demo_override",
        )

    def assess_recovery(
        self,
        station_id: str,
        *,
        reference_at: datetime | None = None,
    ) -> VentilationAssessment:
        reference_at = self._aware_utc(reference_at or self._clock())
        station_gate = self._station_status_gate(station_id)
        if station_gate:
            return VentilationAssessment(
                eligible=False,
                reason_code=station_gate,
                policy_version=ECO_RECOVERY_POLICY_VERSION,
                required_duration_seconds=self.recovery_duration_seconds,
            )
        source_intent = self._latest_unclosed_boost(station_id)
        if source_intent is None:
            return VentilationAssessment(
                eligible=False,
                reason_code="no_succeeded_boost",
                policy_version=ECO_RECOVERY_POLICY_VERSION,
                required_duration_seconds=self.recovery_duration_seconds,
            )

        acknowledged_at = source_intent.get("acknowledged_at")
        if source_intent.get("ack_status") != "succeeded" or acknowledged_at is None:
            return VentilationAssessment(
                eligible=False,
                reason_code="boost_acknowledgement_missing",
                policy_version=ECO_RECOVERY_POLICY_VERSION,
                required_duration_seconds=self.recovery_duration_seconds,
                source_command_intent_id=str(source_intent["command_intent_id"]),
                device_id=str(source_intent["device_id"]),
            )
        started_at = self._aware_utc(acknowledged_at)
        if (reference_at - started_at).total_seconds() < self.recovery_duration_seconds:
            return VentilationAssessment(
                eligible=False,
                reason_code="recovery_window_not_elapsed",
                policy_version=ECO_RECOVERY_POLICY_VERSION,
                required_duration_seconds=self.recovery_duration_seconds,
                source_command_intent_id=str(source_intent["command_intent_id"]),
                device_id=str(source_intent["device_id"]),
            )

        rows = self._measurements(
            station_id,
            reference_at=reference_at,
            required_seconds=self.recovery_duration_seconds,
        )
        assessment = self._assess_continuity(
            rows,
            reference_at=reference_at,
            required_seconds=self.recovery_duration_seconds,
            predicate=self._is_safe_measurement,
            policy_version=ECO_RECOVERY_POLICY_VERSION,
            failure_reason="safe_values_not_continuous",
        )
        return VentilationAssessment(
            **{
                **asdict(assessment),
                "source_command_intent_id": str(source_intent["command_intent_id"]),
                "device_id": str(source_intent["device_id"]),
            }
        )

    def _measurements(
        self,
        station_id: str,
        *,
        reference_at: datetime,
        required_seconds: int,
    ) -> list[dict[str, Any]]:
        window_start = reference_at - timedelta(seconds=required_seconds + self.max_gap_seconds)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT measured_at, pm25, co2, quality_flag
                    FROM measurements
                    WHERE station_id = %s
                      AND quality_flag = 'valid'
                      AND measured_at >= %s
                      AND measured_at <= %s
                    ORDER BY measured_at ASC
                    """,
                    (station_id, window_start, reference_at),
                )
                return [dict(row) for row in cur.fetchall()]

    def _latest_unclosed_boost(self, station_id: str) -> dict[str, Any] | None:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT intent.command_intent_id, intent.device_id, intent.created_at,
                           intent.acknowledged_at, intent.ack_status
                    FROM device_command_intents AS intent
                    WHERE intent.station_id = %s
                      AND intent.command IN ('ventilation_boost', 'air_purifier_on')
                      AND intent.status = 'succeeded'
                      AND NOT EXISTS (
                          SELECT 1
                          FROM device_command_intents AS eco
                          WHERE eco.station_id = intent.station_id
                            AND eco.device_id = intent.device_id
                            AND eco.command = 'eco_mode'
                            AND eco.created_at > intent.created_at
                      )
                    ORDER BY intent.created_at DESC
                    LIMIT 1
                    """,
                    (station_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def _station_status_gate(self, station_id: str) -> str | None:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    "SELECT status FROM station_status WHERE station_id = %s",
                    (station_id,),
                )
                row = cur.fetchone()
        if not row:
            return "station_status_unavailable"
        status = str(row.get("status") or "invalid").lower()
        return None if status == "online" else f"station_{status}"

    def _assess_continuity(
        self,
        rows: list[dict[str, Any]],
        *,
        reference_at: datetime,
        required_seconds: int,
        predicate: Callable[[dict[str, Any]], bool],
        policy_version: str,
        failure_reason: str,
    ) -> VentilationAssessment:
        sequence = self._trailing_sequence(rows, reference_at=reference_at, predicate=predicate)
        if not sequence:
            return VentilationAssessment(False, failure_reason, policy_version, required_seconds)
        window_start = self._aware_utc(sequence[0]["measured_at"])
        window_end = self._aware_utc(sequence[-1]["measured_at"])
        continuous_seconds = max(0, int((reference_at - window_start).total_seconds()))
        if continuous_seconds < required_seconds:
            return VentilationAssessment(
                False,
                "continuous_window_too_short",
                policy_version,
                required_seconds,
                continuous_seconds,
                window_start,
                window_end,
            )
        return VentilationAssessment(
            True,
            "eligible",
            policy_version,
            required_seconds,
            continuous_seconds,
            window_start,
            window_end,
        )

    def _trailing_sequence(
        self,
        rows: list[dict[str, Any]],
        *,
        reference_at: datetime,
        predicate: Callable[[dict[str, Any]], bool],
    ) -> list[dict[str, Any]]:
        ordered = sorted(rows, key=lambda row: self._aware_utc(row["measured_at"]))
        if not ordered or not predicate(ordered[-1]):
            return []
        latest_at = self._aware_utc(ordered[-1]["measured_at"])
        latest_age = (reference_at - latest_at).total_seconds()
        if latest_age < 0 or latest_age > self.max_gap_seconds or latest_age > self.stale_after_seconds:
            return []

        sequence = [ordered[-1]]
        newer_at = latest_at
        for row in reversed(ordered[:-1]):
            measured_at = self._aware_utc(row["measured_at"])
            if (newer_at - measured_at).total_seconds() > self.max_gap_seconds:
                break
            if not predicate(row):
                break
            sequence.append(row)
            newer_at = measured_at
        sequence.reverse()
        return sequence

    def _is_trigger_measurement(self, row: dict[str, Any]) -> bool:
        pm25 = row.get("pm25")
        co2 = row.get("co2")
        return (pm25 is not None and float(pm25) > self.pm25_threshold) or (
            co2 is not None and float(co2) > self.co2_threshold
        )

    def _is_safe_measurement(self, row: dict[str, Any]) -> bool:
        pm25 = row.get("pm25")
        co2 = row.get("co2")
        return (
            pm25 is not None
            and co2 is not None
            and float(pm25) <= self.pm25_threshold
            and float(co2) <= self.co2_threshold
        )

    @staticmethod
    def _aware_utc(value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("measurement timestamps must be timezone-aware")
        return value.astimezone(UTC)
