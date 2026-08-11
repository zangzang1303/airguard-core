from __future__ import annotations

import psycopg2
from typing import Any
from uuid import UUID, uuid4

from .audit_service import AuditService
from .database import Database, ServiceError, dict_cursor


class ApprovalStoreUnavailableError(Exception):
    """Raised when the approval store cannot be reached."""


class ApprovalService:
    def __init__(self, db: Database, audit: AuditService) -> None:
        self.db = db
        self.audit = audit

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
                request_id = str(uuid4())
                cur.execute(
                    """
                    INSERT INTO approval_requests (
                        request_id, request_type, station_id, device_id, proposed_action,
                        reason, evidence, status, version, created_by, idempotency_key
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, 'pending', 1, %s, %s)
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
                        __import__("json").dumps(evidence, ensure_ascii=True, default=str),
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
                    actor_type="agent" if created_by == "ai_agent" else "user",
                    actor_id=created_by,
                    actor_role="agent" if created_by == "ai_agent" else None,
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
            clauses.append("status = %s")
            params.append(status)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    f"""
                    SELECT request_id, request_type, station_id, device_id, proposed_action, reason,
                           evidence, status, version, created_by, created_at, reviewed_by,
                           reviewed_at, review_note
                    FROM approval_requests
                    {where}
                    ORDER BY created_at DESC
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]

    def get_request(self, request_id: str) -> dict[str, Any]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute("SELECT * FROM approval_requests WHERE request_id = %s", (request_id,))
                row = cur.fetchone()
                if not row:
                    raise ServiceError("approval_not_found", "Approval request was not found", 404)
                return dict(row)

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
        self._require_manager(reviewer_role)
        reviewer_uuid = self._validate_user_id(reviewer_id)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                self._ensure_user(cur, reviewer_uuid, reviewer_role)
                cur.execute(
                    """
                    UPDATE approval_requests
                    SET status = 'approved', reviewed_by = %s, reviewed_at = NOW(),
                        review_note = %s, version = version + 1
                    WHERE request_id = %s AND status = 'pending' AND version = %s
                    RETURNING *
                    """,
                    (reviewer_uuid, note, request_id, expected_version),
                )
                request = cur.fetchone()
                if not request:
                    self._raise_transition_error(cur, request_id)
                approved = dict(request)
                command_intent = self._create_dispatch_intent(cur, approved)
                audit_ref = self.audit.record(
                    actor_type="user",
                    actor_id=reviewer_uuid,
                    actor_role=reviewer_role,
                    action="approval.approve",
                    entity_type="approval_request",
                    entity_id=request_id,
                    correlation_id=correlation_id,
                    details={"command_intent_id": command_intent.get("command_intent_id") if command_intent else None},
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
                        review_note = %s, version = version + 1
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

    def require_approved_device_action(self, request_id: str, device_id: str, command: str) -> bool:
        try:
            UUID(request_id)
        except ValueError:
            return False
        try:
            with self.db.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT 1 FROM approval_requests
                        WHERE request_id = %s AND device_id = %s AND proposed_action = %s AND status = 'approved'
                        """,
                        (request_id, device_id, command),
                    )
                    return cur.fetchone() is not None
        except psycopg2.Error as exc:
            raise ApprovalStoreUnavailableError(str(exc)) from exc

    def record_device_dispatch(
        self,
        *,
        request_id: str,
        device_id: str,
        status: str,
        correlation_id: str | None,
        error: str | None = None,
    ) -> None:
        """Persist a dispatch outcome; device acknowledgement remains a separate MQTT event."""
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE device_command_intents
                    SET status = %s, dispatched_at = NOW(), dispatch_error = %s
                    WHERE approval_request_id = %s AND device_id = %s
                    """,
                    (status, error, request_id, device_id),
                )
                self.audit.record(
                    actor_type="system",
                    actor_role="backend",
                    action="device_command.dispatch" if status == "published" else "device_command.dispatch.failure",
                    entity_type="approval_request",
                    entity_id=request_id,
                    correlation_id=correlation_id,
                    outcome="success" if status == "published" else "failure",
                    details={"device_id": device_id, "status": status, "error": error},
                    conn=conn,
                )

    def _create_dispatch_intent(self, cur, request: dict[str, Any]) -> dict[str, Any] | None:
        if not request.get("device_id"):
            return None
        command_intent_id = str(uuid4())
        cur.execute(
            """
            INSERT INTO device_command_intents (
                command_intent_id, approval_request_id, device_id, station_id,
                command, status, idempotency_key
            )
            VALUES (%s, %s, %s, %s, %s, 'queued', %s)
            RETURNING command_intent_id, approval_request_id, device_id, station_id,
                      command, status, idempotency_key, created_at
            """,
            (
                command_intent_id,
                request["request_id"],
                request.get("device_id"),
                request.get("station_id"),
                request.get("proposed_action"),
                f"approval:{request['request_id']}:v{request['version']}",
            ),
        )
        return dict(cur.fetchone())

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        try:
            return str(UUID(user_id))
        except ValueError as exc:
            raise ServiceError("invalid_user_id", "X-User-ID must be a UUID", 422) from exc

    @staticmethod
    def _ensure_user(cur, user_id: str, role: str) -> None:
        cur.execute(
            """
            INSERT INTO users (user_id, email, role, full_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET role = EXCLUDED.role
            """,
            (user_id, f"{user_id}@local.airguard", role, "Demo Manager"),
        )
    @staticmethod
    def _require_manager(role: str) -> None:
        if role != "manager":
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


def require_approved_device_action(request_id: str, device_id: str, command: str) -> bool:
    if _default_service is None:
        return False
    return _default_service.require_approved_device_action(request_id, device_id, command)


def record_device_dispatch(
    request_id: str,
    device_id: str,
    status: str,
    correlation_id: str | None,
    error: str | None = None,
) -> None:
    if _default_service is None:
        raise ApprovalStoreUnavailableError("approval service is not configured")
    _default_service.record_device_dispatch(
        request_id=request_id,
        device_id=device_id,
        status=status,
        correlation_id=correlation_id,
        error=error,
    )





