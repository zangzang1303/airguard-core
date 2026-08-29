from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import uuid4

from psycopg2.extras import Json

from .database import Database, ServiceError, dict_cursor
from .report_policy import REPORT_SCHEMA_VERSION

DEFAULT_REPORT_LEASE_SECONDS = 300


@dataclass(frozen=True)
class ReportSourceData:
    measurements: list[dict[str, Any]]
    alerts: list[dict[str, Any]]
    approvals: list[dict[str, Any]]
    command_intents: list[dict[str, Any]]
    device_status_events: list[dict[str, Any]]
    active_station_ids: list[str] = field(default_factory=list)
    device_profiles: list[dict[str, Any]] = field(default_factory=list)


class ReportRepository(Protocol):
    def reserve_report(
        self,
        *,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        timezone_name: str,
        generated_by: str | None,
    ) -> tuple[dict[str, Any], bool]: ...

    def load_source_data(self, *, period_start: datetime, period_end: datetime) -> ReportSourceData: ...

    def complete_report(
        self,
        *,
        report_id: str,
        generation_attempt_id: str,
        statistics: dict[str, Any],
        evidence_summary: dict[str, Any],
        narrative: str,
        generation_mode: str,
        model_source: str,
        failure_code: str | None,
        schema_version: str,
        content_checksum_sha256: str,
    ) -> dict[str, Any]: ...

    def fail_report(self, *, report_id: str, generation_attempt_id: str, failure_code: str) -> dict[str, Any]: ...

    def list_reports(
        self,
        *,
        report_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]: ...

    def get_report(self, report_id: str) -> dict[str, Any]: ...


class PostgresReportRepository:
    """PostgreSQL persistence boundary for deterministic environmental reports.

    Source queries deliberately select operational/environmental fields only. User email,
    actor identity, session data, credentials and raw audit metadata never enter report input.
    """

    def __init__(self, db: Database, *, lease_seconds: int = DEFAULT_REPORT_LEASE_SECONDS) -> None:
        if lease_seconds < 1 or lease_seconds > 3600:
            raise ValueError("lease_seconds must be between 1 and 3600")
        self.db = db
        self.lease_seconds = lease_seconds

    def reserve_report(
        self,
        *,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        timezone_name: str,
        generated_by: str | None,
    ) -> tuple[dict[str, Any], bool]:
        report_id = str(uuid4())
        generation_attempt_id = str(uuid4())
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        INSERT INTO environmental_reports AS existing_report (
                            report_id, report_type, period_start, period_end, timezone,
                            status, statistics, evidence_summary, generation_mode,
                            model_source, generated_by, generation_attempt_id,
                            lease_expires_at, schema_version, content_checksum_sha256
                        )
                        VALUES (%s, %s, %s, %s, %s, 'generating', %s, %s,
                                'deterministic_grounded', 'backend_deterministic_report_v1',
                                %s, %s, NOW() + (%s * INTERVAL '1 second'), %s, NULL)
                        ON CONFLICT (report_type, period_start, period_end, timezone)
                        DO UPDATE SET
                            status = 'generating',
                            statistics = '{}'::JSONB,
                            evidence_summary = '{}'::JSONB,
                            narrative = NULL,
                            generation_mode = 'deterministic_grounded',
                            model_source = 'backend_deterministic_report_v1',
                            generated_by = COALESCE(EXCLUDED.generated_by, existing_report.generated_by),
                            failure_code = NULL,
                            schema_version = EXCLUDED.schema_version,
                            content_checksum_sha256 = NULL,
                            completed_at = NULL,
                            generation_attempt_id = EXCLUDED.generation_attempt_id,
                            lease_expires_at = EXCLUDED.lease_expires_at
                        WHERE existing_report.status = 'failed'
                           OR (
                               existing_report.status = 'generating'
                               AND (
                                   existing_report.lease_expires_at IS NULL
                                   OR existing_report.lease_expires_at <= NOW()
                               )
                           )
                        RETURNING *
                        """,
                        (
                            report_id,
                            report_type,
                            period_start,
                            period_end,
                            timezone_name,
                            Json({}),
                            Json({}),
                            generated_by,
                            generation_attempt_id,
                            self.lease_seconds,
                            REPORT_SCHEMA_VERSION,
                        ),
                    )
                    inserted = cur.fetchone()
                    if inserted:
                        return dict(inserted), True
                    cur.execute(
                        """
                        SELECT * FROM environmental_reports
                        WHERE report_type = %s AND period_start = %s
                          AND period_end = %s AND timezone = %s
                        """,
                        (report_type, period_start, period_end, timezone_name),
                    )
                    existing = cur.fetchone()
                    if existing:
                        return dict(existing), False
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                "report_store_unavailable",
                "The environmental report store is unavailable.",
                503,
            ) from exc
        raise ServiceError("report_reservation_conflict", "The report could not be reserved.", 409)

    def load_source_data(self, *, period_start: datetime, period_end: datetime) -> ReportSourceData:
        lookback_start = period_start - timedelta(days=1)
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        SELECT station_id, measured_at, pm25, co2, noise_db, temperature,
                               source, quality_flag
                        FROM measurements
                        WHERE measured_at >= %s AND measured_at < %s
                        ORDER BY measured_at, station_id
                        """,
                        (lookback_start, period_end),
                    )
                    measurements = [dict(row) for row in cur.fetchall()]

                    cur.execute(
                        """
                        SELECT alert_id, station_id, alert_type, rule_version, severity,
                               observed_value, threshold_value, status, created_at, resolved_at
                        FROM alerts
                        WHERE created_at >= %s AND created_at < %s
                        ORDER BY created_at, alert_id
                        """,
                        (period_start, period_end),
                    )
                    alerts = [dict(row) for row in cur.fetchall()]

                    cur.execute(
                        """
                        SELECT request_id, request_type, station_id, device_id, proposed_action,
                               duration_minutes, status, created_at, reviewed_at
                        FROM approval_requests
                        WHERE created_at >= %s AND created_at < %s
                        ORDER BY created_at, request_id
                        """,
                        (period_start, period_end),
                    )
                    approvals = [dict(row) for row in cur.fetchall()]

                    cur.execute(
                        """
                        SELECT ci.command_intent_id, ci.approval_request_id, ci.device_id,
                               ci.station_id, ci.command, ci.status, ci.duration_minutes,
                               ci.intensity_percent, ci.command_id, ci.created_at,
                               ci.dispatched_at, ci.acknowledged_at, ci.ack_status,
                               ci.device_state, ar.proposed_action AS approval_action,
                               ar.duration_minutes AS approval_duration_minutes
                        FROM device_command_intents ci
                        JOIN approval_requests ar ON ar.request_id = ci.approval_request_id
                        WHERE ci.created_at >= %s AND ci.created_at < %s
                        ORDER BY ci.created_at, ci.command_intent_id
                        """,
                        (lookback_start, period_end),
                    )
                    command_intents = [dict(row) for row in cur.fetchall()]

                    cur.execute(
                        """
                        SELECT event_id, command_id, command_intent_id, device_id, status,
                               device_state, observed_at, is_simulated
                        FROM device_status_events
                        WHERE observed_at >= %s AND observed_at < %s
                        ORDER BY observed_at, device_id
                        """,
                        (lookback_start, period_end),
                    )
                    device_status_events = [dict(row) for row in cur.fetchall()]

                    cur.execute(
                        """
                        SELECT station_id FROM stations
                        WHERE active = TRUE
                        ORDER BY station_id
                        """
                    )
                    active_station_ids = [str(row["station_id"]) for row in cur.fetchall()]

                    cur.execute(
                        """
                        SELECT profile_id, device_id, profile_version, effective_from,
                               effective_to, airflow_m3_per_hour, boost_power_kw,
                               eco_power_kw, calibration_source, is_simulated, created_at
                        FROM device_operating_profiles
                        WHERE effective_from < %s
                          AND (effective_to IS NULL OR effective_to > %s)
                        ORDER BY device_id, effective_from, profile_version
                        """,
                        (period_end, lookback_start),
                    )
                    device_profiles = [dict(row) for row in cur.fetchall()]
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                "report_source_unavailable",
                "Environmental report source data is unavailable.",
                503,
            ) from exc
        return ReportSourceData(
            measurements=measurements,
            alerts=alerts,
            approvals=approvals,
            command_intents=command_intents,
            device_status_events=device_status_events,
            active_station_ids=active_station_ids,
            device_profiles=device_profiles,
        )

    def complete_report(
        self,
        *,
        report_id: str,
        generation_attempt_id: str,
        statistics: dict[str, Any],
        evidence_summary: dict[str, Any],
        narrative: str,
        generation_mode: str,
        model_source: str,
        failure_code: str | None,
        schema_version: str,
        content_checksum_sha256: str,
    ) -> dict[str, Any]:
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        UPDATE environmental_reports
                        SET status = 'completed', statistics = %s, evidence_summary = %s,
                            narrative = %s, generation_mode = %s, model_source = %s,
                            failure_code = %s, schema_version = %s,
                            content_checksum_sha256 = %s, completed_at = NOW(),
                            generation_attempt_id = NULL, lease_expires_at = NULL
                        WHERE report_id = %s AND generation_attempt_id = %s
                          AND status = 'generating'
                        RETURNING *
                        """,
                        (
                            Json(statistics),
                            Json(evidence_summary),
                            narrative,
                            generation_mode,
                            model_source,
                            failure_code,
                            schema_version,
                            content_checksum_sha256,
                            report_id,
                            generation_attempt_id,
                        ),
                    )
                    row = cur.fetchone()
                    if row:
                        return dict(row)
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError("report_store_unavailable", "The report could not be persisted.", 503) from exc
        raise ServiceError(
            "report_generation_lease_lost",
            "This report generation attempt no longer owns the report lease.",
            409,
        )

    def fail_report(
        self,
        *,
        report_id: str,
        generation_attempt_id: str,
        failure_code: str,
    ) -> dict[str, Any]:
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        UPDATE environmental_reports
                        SET status = 'failed', failure_code = %s, completed_at = NOW(),
                            generation_attempt_id = NULL, lease_expires_at = NULL
                        WHERE report_id = %s AND generation_attempt_id = %s
                          AND status = 'generating'
                        RETURNING *
                        """,
                        (failure_code, report_id, generation_attempt_id),
                    )
                    row = cur.fetchone()
                    if row:
                        return dict(row)
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                "report_store_unavailable", "The report failure state could not be persisted.", 503
            ) from exc
        raise ServiceError(
            "report_generation_lease_lost",
            "This report generation attempt no longer owns the report lease.",
            409,
        )

    def list_reports(
        self,
        *,
        report_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        where = "WHERE report_type = %s" if report_type else ""
        params: list[Any] = [report_type] if report_type else []
        params.extend([limit, offset])
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM environmental_reports
                        {where}
                        ORDER BY period_end DESC, created_at DESC
                        LIMIT %s OFFSET %s
                        """,
                        params,
                    )
                    return [dict(row) for row in cur.fetchall()]
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError("report_store_unavailable", "Environmental reports are unavailable.", 503) from exc

    def get_report(self, report_id: str) -> dict[str, Any]:
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute("SELECT * FROM environmental_reports WHERE report_id = %s", (report_id,))
                    row = cur.fetchone()
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError("report_store_unavailable", "The environmental report is unavailable.", 503) from exc
        if not row:
            raise ServiceError("report_not_found", "The environmental report was not found.", 404)
        return dict(row)
