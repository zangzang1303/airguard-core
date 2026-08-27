from __future__ import annotations

import json
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import psycopg2

from .audit_service import AuditService
from .database import Database, ServiceError, dict_cursor
from .ventilation_service import ALLOWED_DEVICE_ACTIONS, TIMED_DEVICE_ACTIONS, VentilationService


class ApprovalStoreUnavailableError(Exception):
    """Raised when the approval store cannot be reached."""


def stable_device_command_id(
    approval_request_id: str,
    device_id: str,
    command: str,
    idempotency_key: str,
) -> str:
    material = "|".join((approval_request_id, device_id, command, idempotency_key))
    return str(uuid5(NAMESPACE_URL, f"airguard-device-command:{material}"))


class ApprovalService:
    DEFAULT_DURATION_MINUTES = 45
    DEFAULT_INTENSITY_PERCENT = 80
    MIN_DURATION_MINUTES = 5
    MAX_DURATION_MINUTES = 180

    def __init__(
        self,
        db: Database,
        audit: AuditService,
        *,
        pending_ttl_seconds: int = 3600,
        default_duration_minutes: int = 45,
        default_intensity_percent: int = 80,
        ventilation_service: VentilationService | None = None,
    ) -> None:
        if not self.MIN_DURATION_MINUTES <= default_duration_minutes <= self.MAX_DURATION_MINUTES:
            raise ValueError("default_duration_minutes must be between 5 and 180")
        if not 1 <= default_intensity_percent <= 100:
            raise ValueError("default_intensity_percent must be between 1 and 100")
        self.db = db
        self.audit = audit
        self.pending_ttl_seconds = pending_ttl_seconds
        self.default_duration_minutes = default_duration_minutes
        self.default_intensity_percent = default_intensity_percent
        self.ventilation_service = ventilation_service or VentilationService(
            db,
            default_duration_minutes=default_duration_minutes,
            default_intensity_percent=default_intensity_percent,
        )

    def create_request(
        self,
        *,
        request_type: str,
        station_id: str | None,
        device_id: str | None,
        proposed_action: str,
        reason: str,
        evidence: dict[str, Any],
        created_by: str,
        correlation_id: str | None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        normalized_evidence = dict(evidence)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                if idempotency_key:
                    cur.execute(
                        "SELECT * FROM approval_requests WHERE idempotency_key = %s",
                        (idempotency_key,),
                    )
                    existing = cur.fetchone()
                    if existing:
                        return {**dict(existing), "reused": True}
                device_id, normalized_evidence = self._normalize_device_request(
                    cur,
                    station_id=station_id,
                    requested_device_id=device_id,
                    proposed_action=proposed_action,
                    evidence=normalized_evidence,
                )
                control = normalized_evidence.get("control", {})
                request_id = str(uuid4())
                cur.execute(
                    """
                    INSERT INTO approval_requests (
                        request_id, request_type, station_id, device_id, proposed_action,
                        reason, evidence, duration_minutes, intensity_percent,
                        status, version, created_by, idempotency_key
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, 'pending', 1, %s, %s)
                    ON CONFLICT (idempotency_key) WHERE idempotency_key IS NOT NULL DO NOTHING
                    RETURNING *
                    """,
                    (
                        request_id,
                        request_type,
                        station_id,
                        device_id,
                        proposed_action,
                        reason,
                        json.dumps(normalized_evidence, ensure_ascii=True, default=str),
                        control.get("duration_minutes"),
                        control.get("intensity_percent"),
                        created_by,
                        idempotency_key,
                    ),
                )
                inserted = cur.fetchone()
                if not inserted and idempotency_key:
                    cur.execute("SELECT * FROM approval_requests WHERE idempotency_key = %s", (idempotency_key,))
                    existing = cur.fetchone()
                    if existing:
                        return {**dict(existing), "reused": True}
                    raise ServiceError("proposal_conflict", "Proposal idempotency conflict", 409)
                request = dict(inserted)
                self.audit.record(
                    actor_type=(
                        "agent" if created_by == "ai_agent"
                        else "system" if created_by.startswith("system")
                        else "user"
                    ),
                    actor_id=created_by,
                    actor_role=(
                        "agent" if created_by == "ai_agent"
                        else "backend" if created_by.startswith("system")
                        else None
                    ),
                    action="approval.create",
                    entity_type="approval_request",
                    entity_id=str(request_id),
                    correlation_id=correlation_id,
                    details={"station_id": station_id, "device_id": device_id, "proposed_action": proposed_action},
                    conn=conn,
                )
                return request

    def list_requests(self, *, status: str | None = None) -> list[dict[str, Any]]:
        clauses = []
        params: list[Any] = []
        if status:
            clauses.append("approval_requests.status = %s")
            params.append(status)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        f"""
                        SELECT request_id, request_type, station_id, device_id, proposed_action, reason,
                               evidence, duration_minutes, intensity_percent, status, version,
                               created_by, approval_requests.created_at,
                               reviewed_by, reviewed_at, review_note, intent.command_intent
                        FROM approval_requests
                        LEFT JOIN LATERAL (
                            SELECT to_jsonb(device_command_intents.*) AS command_intent
                            FROM device_command_intents
                            WHERE approval_request_id = approval_requests.request_id
                            ORDER BY created_at DESC
                            LIMIT 1
                        ) AS intent ON TRUE
                        {where}
                        ORDER BY approval_requests.created_at DESC
                        """,
                        params,
                    )
                    return [dict(row) for row in cur.fetchall()]
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError("approval_store_unavailable", "Approval store is unavailable", 503) from exc

    def get_request(self, request_id: str) -> dict[str, Any]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT approval_requests.*, intent.command_intent
                    FROM approval_requests
                    LEFT JOIN LATERAL (
                        SELECT to_jsonb(device_command_intents.*) AS command_intent
                        FROM device_command_intents
                        WHERE approval_request_id = approval_requests.request_id
                        ORDER BY created_at DESC
                        LIMIT 1
                    ) AS intent ON TRUE
                    WHERE request_id = %s
                    """,
                    (request_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ServiceError("approval_not_found", "Approval request was not found", 404)
                return dict(row)

    def has_request_for_alert(self, *, station_id: str, alert_created_at: Any) -> bool:
        """Avoid repeated LLM runs for the same active-alert lifecycle."""
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM approval_requests
                    WHERE request_type = 'warning_proposal'
                      AND station_id = %s
                      AND created_at >= %s
                    LIMIT 1
                    """,
                    (station_id, alert_created_at),
                )
                return cur.fetchone() is not None

    def has_pending_warning_proposal(self, *, station_id: str) -> bool:
        """Keep the manager queue to one unresolved automatic proposal per station."""
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM approval_requests
                    WHERE request_type = 'warning_proposal'
                      AND station_id = %s
                      AND status = 'pending'
                    LIMIT 1
                    """,
                    (station_id,),
                )
                return cur.fetchone() is not None

    def expire_pending_requests(self, *, correlation_id: str | None = None) -> int:
        """Expire unreviewed proposals while preserving them and their audit trail."""
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        UPDATE approval_requests
                        SET status = 'expired', reviewed_at = NOW(),
                            review_note = 'Expired automatically after the manager review window elapsed.',
                            version = version + 1
                        WHERE status = 'pending'
                          AND created_at < NOW() - (%s * INTERVAL '1 second')
                        RETURNING request_id, station_id
                        """,
                        (self.pending_ttl_seconds,),
                    )
                    expired = [dict(row) for row in cur.fetchall()]
                    for expired_request in expired:
                        self.audit.record(
                            actor_type="system",
                            actor_role="backend",
                            action="approval.expire",
                            entity_type="approval_request",
                            entity_id=str(expired_request["request_id"]),
                            correlation_id=correlation_id,
                            outcome="expired",
                            details={
                                "station_id": expired_request["station_id"],
                                "ttl_seconds": self.pending_ttl_seconds,
                                "reason": "manager_review_window_elapsed",
                            },
                            conn=conn,
                        )
                    return len(expired)
        except Exception:
            return 0

    def approve(
        self,
        *,
        request_id: str,
        expected_version: int,
        reviewer_id: str,
        reviewer_role: str,
        note: str | None,
        correlation_id: str | None,
    ) -> dict[str, Any]:
        return self._approve_request(
            request_id=request_id,
            expected_version=expected_version,
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            note=note,
            correlation_id=correlation_id,
            audit_action="approval.approve",
            idempotency_key=None,
        )

    def quick_approve(
        self,
        *,
        request_id: str,
        expected_version: int,
        reviewer_id: str,
        reviewer_role: str,
        note: str | None,
        correlation_id: str | None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Use the normal HITL transition with retry-safe quick-action semantics."""
        if len(idempotency_key.strip()) < 8:
            raise ServiceError("invalid_idempotency_key", "Idempotency key must be at least 8 characters", 422)
        return self._approve_request(
            request_id=request_id,
            expected_version=expected_version,
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            note=note,
            correlation_id=correlation_id,
            audit_action="approval.quick_approve",
            idempotency_key=idempotency_key.strip(),
        )

    def _approve_request(
        self,
        *,
        request_id: str,
        expected_version: int,
        reviewer_id: str,
        reviewer_role: str,
        note: str | None,
        correlation_id: str | None,
        audit_action: str,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        self._require_manager(reviewer_role)
        reviewer_uuid = self._validate_user_id(reviewer_id)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                if idempotency_key:
                    reused = self._find_quick_approval(cur, request_id, idempotency_key)
                    if reused:
                        return reused
                self._ensure_user(cur, reviewer_uuid, reviewer_role)
                cur.execute(
                    """
                    UPDATE approval_requests
                    SET status = 'approved', reviewed_by = %s, reviewed_at = NOW(),
                        review_note = %s, review_mode = %s,
                        review_idempotency_key = %s, version = version + 1
                    WHERE request_id = %s AND status = 'pending' AND version = %s
                    RETURNING *
                    """,
                    (
                        reviewer_uuid,
                        note,
                        "quick" if idempotency_key else "standard",
                        idempotency_key,
                        request_id,
                        expected_version,
                    ),
                )
                request = cur.fetchone()
                if not request:
                    if idempotency_key:
                        reused = self._find_quick_approval(cur, request_id, idempotency_key)
                        if reused:
                            return reused
                    self._raise_transition_error(cur, request_id)
                approved = dict(request)
                command_intent = self._create_dispatch_intent(cur, approved)
                audit_details = {
                    "command_intent_id": command_intent.get("command_intent_id") if command_intent else None,
                }
                if idempotency_key:
                    audit_details["idempotency_key"] = idempotency_key
                audit_ref = self.audit.record(
                    actor_type="user",
                    actor_id=reviewer_uuid,
                    actor_role=reviewer_role,
                    action=audit_action,
                    entity_type="approval_request",
                    entity_id=request_id,
                    correlation_id=correlation_id,
                    details=audit_details,
                    conn=conn,
                )
                return {**approved, "audit_ref": audit_ref, "command_intent": command_intent}

    def reject(
        self,
        *,
        request_id: str,
        expected_version: int,
        reviewer_id: str,
        reviewer_role: str,
        note: str,
        correlation_id: str | None,
    ) -> dict[str, Any]:
        self._require_manager(reviewer_role)
        reviewer_uuid = self._validate_user_id(reviewer_id)
        if not note.strip():
            raise ServiceError("review_note_required", "Reject note is required", 422)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                self._ensure_user(cur, reviewer_uuid, reviewer_role)
                cur.execute(
                    """
                    UPDATE approval_requests
                    SET status = 'rejected', reviewed_by = %s, reviewed_at = NOW(),
                        review_note = %s, review_mode = 'standard',
                        review_idempotency_key = NULL, version = version + 1
                    WHERE request_id = %s AND status = 'pending' AND version = %s
                    RETURNING *
                    """,
                    (reviewer_uuid, note, request_id, expected_version),
                )
                request = cur.fetchone()
                if not request:
                    self._raise_transition_error(cur, request_id)
                rejected = dict(request)
                audit_ref = self.audit.record(
                    actor_type="user",
                    actor_id=reviewer_uuid,
                    actor_role=reviewer_role,
                    action="approval.reject",
                    entity_type="approval_request",
                    entity_id=request_id,
                    correlation_id=correlation_id,
                    details={"review_note": note},
                    conn=conn,
                )
                return {**rejected, "audit_ref": audit_ref, "command_intent": None}

    def require_approved_device_action(
        self,
        request_id: str,
        device_id: str,
        command: str,
    ) -> dict[str, Any] | None:
        try:
            UUID(request_id)
        except ValueError:
            return None
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        SELECT approval_requests.request_id, approval_requests.station_id,
                               approval_requests.device_id, approval_requests.proposed_action,
                               approval_requests.evidence, approval_requests.duration_minutes,
                               approval_requests.intensity_percent, approval_requests.status,
                               intent.command_intent_id, intent.command_id,
                               intent.command_intent_status, intent.ack_status
                        FROM approval_requests
                        LEFT JOIN LATERAL (
                            SELECT command_intent_id, command_id,
                                   status AS command_intent_status, ack_status
                            FROM device_command_intents
                            WHERE approval_request_id = approval_requests.request_id
                              AND device_id = approval_requests.device_id
                            ORDER BY created_at DESC
                            LIMIT 1
                        ) AS intent ON TRUE
                        WHERE approval_requests.request_id = %s
                          AND approval_requests.device_id = %s
                          AND approval_requests.proposed_action = %s
                          AND approval_requests.status = 'approved'
                        """,
                        (request_id, device_id, command),
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None
        except psycopg2.Error as exc:
            raise ApprovalStoreUnavailableError(str(exc)) from exc
        except ServiceError as exc:
            if exc.status_code >= 500:
                raise ApprovalStoreUnavailableError(str(exc)) from exc
            raise

    def record_device_dispatch(
        self,
        *,
        request_id: str,
        device_id: str,
        status: str,
        correlation_id: str | None,
        error: str | None = None,
        command_id: str | None = None,
    ) -> None:
        """Persist a dispatch outcome; device acknowledgement remains a separate MQTT event."""
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        UPDATE device_command_intents
                        SET status = CASE
                                WHEN status = 'succeeded' OR ack_status = 'succeeded' THEN status
                                ELSE %s
                            END,
                            dispatched_at = CASE
                                WHEN status = 'succeeded' OR ack_status = 'succeeded' THEN dispatched_at
                                ELSE NOW()
                            END,
                            dispatch_error = CASE
                                WHEN status = 'succeeded' OR ack_status = 'succeeded' THEN dispatch_error
                                ELSE %s
                            END,
                            command_id = COALESCE(command_id, %s)
                        WHERE approval_request_id = %s AND device_id = %s
                        """,
                        (status, error, command_id, request_id, device_id),
                    )
                self.audit.record(
                    actor_type="system",
                    actor_role="backend",
                    action={
                        "enqueued": "device_command.dispatch.enqueued",
                        "publishing": "device_command.dispatch.prepare",
                        "published": "device_command.dispatch",
                    }.get(status, "device_command.dispatch.failure"),
                    entity_type="approval_request",
                    entity_id=request_id,
                    correlation_id=correlation_id,
                    outcome="success" if status in {"enqueued", "publishing", "published"} else "failure",
                    details={
                        "device_id": device_id,
                        "status": status,
                        "error": error,
                        "command_id": command_id,
                    },
                    conn=conn,
                )
        except psycopg2.Error as exc:
            raise ApprovalStoreUnavailableError(str(exc)) from exc
        except ServiceError as exc:
            if exc.status_code >= 500:
                raise ApprovalStoreUnavailableError(str(exc)) from exc
            raise

    def list_dispatch_candidates(self, *, limit: int = 50) -> list[dict[str, Any]]:
        """Return approved intents that have not reached the dispatcher or need a safe retry."""
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        SELECT intent.command_intent_id, intent.approval_request_id,
                               intent.device_id, intent.command, intent.idempotency_key,
                               intent.status
                        FROM device_command_intents AS intent
                        JOIN approval_requests AS approval
                          ON approval.request_id = intent.approval_request_id
                        WHERE approval.status = 'approved'
                          AND intent.ack_status IS NULL
                          AND (
                               intent.status IN ('queued', 'failed')
                               OR (
                                   intent.status IN ('enqueued', 'publishing')
                                   AND COALESCE(intent.dispatched_at, intent.created_at)
                                       < NOW() - INTERVAL '5 minutes'
                               )
                          )
                        ORDER BY intent.created_at
                        LIMIT %s
                        """,
                        (max(1, min(int(limit), 200)),),
                    )
                    return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as exc:
            raise ApprovalStoreUnavailableError(str(exc)) from exc
        except ServiceError as exc:
            if exc.status_code >= 500:
                raise ApprovalStoreUnavailableError(str(exc)) from exc
            raise

    def claim_dispatch_candidate(self, command_intent_id: str) -> dict[str, Any] | None:
        """Atomically lease one intent before handing it to the Celery broker."""
        try:
            UUID(command_intent_id)
        except ValueError:
            return None
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        UPDATE device_command_intents
                        SET status = 'enqueued', dispatched_at = NOW(), dispatch_error = NULL
                        WHERE command_intent_id = %s
                          AND ack_status IS NULL
                          AND (
                              status IN ('queued', 'failed')
                              OR (
                                  status IN ('enqueued', 'publishing')
                                  AND COALESCE(dispatched_at, created_at)
                                      < NOW() - INTERVAL '5 minutes'
                              )
                          )
                        RETURNING command_intent_id, approval_request_id, device_id,
                                  command, idempotency_key, status
                        """,
                        (command_intent_id,),
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None
        except psycopg2.Error as exc:
            raise ApprovalStoreUnavailableError(str(exc)) from exc
        except ServiceError as exc:
            if exc.status_code >= 500:
                raise ApprovalStoreUnavailableError(str(exc)) from exc
            raise

    def _find_quick_approval(
        self,
        cur: Any,
        request_id: str,
        idempotency_key: str,
    ) -> dict[str, Any] | None:
        cur.execute(
            """
            SELECT approval_requests.*, audit_logs.audit_id, intent.command_intent
            FROM audit_logs
            JOIN approval_requests
              ON approval_requests.request_id::text = audit_logs.entity_id
            LEFT JOIN LATERAL (
                SELECT to_jsonb(device_command_intents.*) AS command_intent
                FROM device_command_intents
                WHERE approval_request_id = approval_requests.request_id
                ORDER BY created_at DESC
                LIMIT 1
            ) AS intent ON TRUE
            WHERE audit_logs.action = 'approval.quick_approve'
              AND audit_logs.entity_id = %s
              AND audit_logs.details ->> 'idempotency_key' = %s
            ORDER BY audit_logs.created_at DESC
            LIMIT 1
            """,
            (request_id, idempotency_key),
        )
        row = cur.fetchone()
        if not row:
            return None
        reused = dict(row)
        audit_id = reused.pop("audit_id", None)
        return {**reused, "audit_ref": {"audit_id": audit_id}, "reused": True}

    def _normalize_device_request(
        self,
        cur: Any,
        *,
        station_id: str | None,
        requested_device_id: str | None,
        proposed_action: str,
        evidence: dict[str, Any],
    ) -> tuple[str | None, dict[str, Any]]:
        if proposed_action not in ALLOWED_DEVICE_ACTIONS:
            if requested_device_id:
                raise ServiceError(
                    "unsupported_device_action",
                    "Device actions must use the configured allow-list",
                    422,
                    {"allowed_actions": sorted(ALLOWED_DEVICE_ACTIONS)},
                )
            return requested_device_id, evidence
        if not station_id:
            raise ServiceError("device_station_required", "Device actions require station_id", 422)

        raw_control = evidence.get("control")
        control = dict(raw_control) if isinstance(raw_control, dict) else {}
        if proposed_action == "eco_mode":
            assessment = self.ventilation_service.assess_recovery(station_id)
            if not assessment.eligible:
                raise ServiceError(
                    "eco_recovery_not_eligible",
                    "Eco mode requires 20 minutes of continuous safe PM2.5 and CO2 data after a succeeded boost",
                    409,
                    {"reason_code": assessment.reason_code},
                )
            requested_source = evidence.get("source_command_intent_id")
            if requested_source and str(requested_source) != assessment.source_command_intent_id:
                raise ServiceError(
                    "eco_recovery_source_mismatch",
                    "Eco recovery evidence does not match the latest eligible boost",
                    409,
                )
        else:
            assessment = self.ventilation_service.assess_trigger(station_id)
            if not assessment.eligible:
                raise ServiceError(
                    "ventilation_not_eligible",
                    "Ventilation requires PM2.5 > 50 or CO2 > 1000 for the configured continuous window",
                    409,
                    {
                        "reason_code": assessment.reason_code,
                        "required_duration_seconds": assessment.required_duration_seconds,
                    },
                )

        duration_minutes: int | None = None
        intensity_percent: int | None = None
        if proposed_action in TIMED_DEVICE_ACTIONS:
            raw_duration = control.get("duration_minutes", self.default_duration_minutes)
            if isinstance(raw_duration, bool) or not isinstance(raw_duration, int):
                raise ServiceError("invalid_duration", "duration_minutes must be an integer", 422)
            if not self.MIN_DURATION_MINUTES <= raw_duration <= self.MAX_DURATION_MINUTES:
                raise ServiceError(
                    "invalid_duration",
                    f"duration_minutes must be between {self.MIN_DURATION_MINUTES} and {self.MAX_DURATION_MINUTES}",
                    422,
                )
            if raw_duration != self.default_duration_minutes:
                raise ServiceError(
                    "device_control_policy_mismatch",
                    "duration_minutes must match the backend ventilation policy",
                    409,
                    {"expected_duration_minutes": self.default_duration_minutes},
                )
            duration_minutes = self.default_duration_minutes
            raw_intensity = control.get("intensity_percent", self.default_intensity_percent)
            if isinstance(raw_intensity, bool) or not isinstance(raw_intensity, int) or not 1 <= raw_intensity <= 100:
                raise ServiceError("invalid_intensity", "intensity_percent must be an integer from 1 to 100", 422)
            if raw_intensity != self.default_intensity_percent:
                raise ServiceError(
                    "device_control_policy_mismatch",
                    "intensity_percent must match the backend ventilation policy",
                    409,
                    {"expected_intensity_percent": self.default_intensity_percent},
                )
            intensity_percent = self.default_intensity_percent

        device_id = self._resolve_device(
            cur,
            station_id=station_id,
            action=proposed_action,
            requested_device_id=requested_device_id,
        )
        normalized = dict(evidence)
        normalized["ventilation_policy"] = assessment.as_evidence()
        normalized["control"] = {
            **control,
            "action": proposed_action,
            "duration_minutes": duration_minutes,
            "intensity_percent": intensity_percent,
            "device_id": device_id,
            "mapping_source": "backend_device_registry",
        }
        return device_id, normalized

    @staticmethod
    def _resolve_device(
        cur: Any,
        *,
        station_id: str,
        action: str,
        requested_device_id: str | None,
    ) -> str:
        params: list[Any] = [station_id]
        requested_clause = ""
        if requested_device_id:
            requested_clause = "AND device_id = %s"
            params.append(requested_device_id)
        preferred_type = "air_filter" if action == "air_purifier_on" else "ventilation_filter"
        params.append(preferred_type)
        cur.execute(
            f"""
            SELECT device_id
            FROM devices
            WHERE station_id = %s
              {requested_clause}
              AND device_type IN ('ventilation_filter', 'air_filter')
            ORDER BY CASE WHEN device_type = %s THEN 0 ELSE 1 END, device_id
            LIMIT 1
            """,
            params,
        )
        row = cur.fetchone()
        if not row:
            raise ServiceError(
                "device_mapping_not_found",
                "No compatible backend-registered device is mapped to the station",
                409,
                {"station_id": station_id, "action": action},
            )
        return str(row["device_id"])

    def _create_dispatch_intent(self, cur, request: dict[str, Any]) -> dict[str, Any] | None:
        if not request.get("device_id"):
            return None
        command_intent_id = str(uuid4())
        cur.execute(
            """
            INSERT INTO device_command_intents (
                command_intent_id, approval_request_id, device_id, station_id,
                command, duration_minutes, intensity_percent, status, idempotency_key
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'queued', %s)
            RETURNING command_intent_id, approval_request_id, device_id, station_id,
                      command, duration_minutes, intensity_percent, status,
                      idempotency_key, command_id, created_at
            """,
            (
                command_intent_id,
                request["request_id"],
                request.get("device_id"),
                request.get("station_id"),
                request.get("proposed_action"),
                request.get("duration_minutes"),
                request.get("intensity_percent"),
                f"approval:{request['request_id']}:v{request['version']}",
            ),
        )
        intent = dict(cur.fetchone())
        return intent

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        try:
            return str(UUID(user_id))
        except ValueError as exc:
            raise ServiceError("invalid_user_id", "User ID must be a valid UUID", 422) from exc

    @staticmethod
    def _ensure_user(cur, user_id: str, role: str) -> None:
        cur.execute(
            """
            INSERT INTO users (user_id, email, role, full_name, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id, f"{user_id}@local.airguard", role, "Manager"),
        )

    @staticmethod
    def _require_manager(role: str) -> None:
        if role not in {"manager", "admin"}:
            raise ServiceError("forbidden", "Only manager role can approve or reject requests", 403)

    @staticmethod
    def _raise_transition_error(cur, request_id: str) -> None:
        cur.execute("SELECT status, version FROM approval_requests WHERE request_id = %s", (request_id,))
        existing = cur.fetchone()
        if not existing:
            raise ServiceError("approval_not_found", "Approval request was not found", 404)
        raise ServiceError(
            "approval_conflict",
            "Approval request was already reviewed or version is stale",
            409,
            {"status": existing["status"], "version": existing["version"]},
        )


_default_service: ApprovalService | None = None


def configure_default_service(service: ApprovalService) -> None:
    global _default_service
    _default_service = service


def get_configured_default_service() -> ApprovalService | None:
    return _default_service


def require_approved_device_action(
    request_id: str,
    device_id: str,
    command: str,
) -> dict[str, Any] | None:
    if _default_service is None:
        return None
    return _default_service.require_approved_device_action(request_id, device_id, command)


def record_device_dispatch(
    request_id: str,
    device_id: str,
    status: str,
    correlation_id: str | None,
    error: str | None = None,
    command_id: str | None = None,
) -> None:
    if _default_service is None:
        raise ApprovalStoreUnavailableError("approval service is not configured")
    _default_service.record_device_dispatch(
        request_id=request_id,
        device_id=device_id,
        status=status,
        correlation_id=correlation_id,
        error=error,
        command_id=command_id,
    )





