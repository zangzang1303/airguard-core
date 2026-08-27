from __future__ import annotations

from typing import Any

from .database import Database, ServiceError, dict_cursor

SENSITIVE_KEYS = {"password", "token", "secret", "api_key", "authorization"}


def redact_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    redacted: dict[str, Any] = {}
    for key, value in metadata.items():
        if any(marker in key.lower() for marker in SENSITIVE_KEYS):
            redacted[key] = "[redacted]"
        else:
            redacted[key] = value
    return redacted


class AuditService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record(
        self,
        *,
        actor_type: str,
        action: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        outcome: str = "success",
        actor_id: str | None = None,
        actor_role: str | None = None,
        correlation_id: str | None = None,
        details: dict[str, Any] | None = None,
        conn=None,
    ) -> dict[str, Any]:
        def write(active_conn):
            with dict_cursor(active_conn) as cur:
                cur.execute(
                    """
                    INSERT INTO audit_logs (
                        actor_type, actor_id, actor_role, action, entity_type, entity_id,
                        outcome, correlation_id, details
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING audit_id, created_at
                    """,
                    (
                        actor_type,
                        actor_id,
                        actor_role,
                        action,
                        entity_type,
                        entity_id,
                        outcome,
                        correlation_id,
                        __import__("json").dumps(redact_metadata(details), ensure_ascii=True, default=str),
                    ),
                )
                return dict(cur.fetchone())

        if conn is not None:
            return write(conn)
        with self.db.connection() as owned_conn:
            return write(owned_conn)

    def list_logs(self, *, entity_type: str | None = None, entity_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        clauses = []
        params: list[Any] = []
        if entity_type:
            clauses.append("entity_type = %s")
            params.append(entity_type)
        if entity_id:
            clauses.append("entity_id = %s")
            params.append(entity_id)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        f"""
                        SELECT audit_id, actor_type, actor_id, actor_role, action, entity_type,
                               entity_id, outcome, correlation_id, details, created_at
                        FROM audit_logs
                        {where}
                        ORDER BY created_at DESC, audit_id DESC
                        LIMIT %s
                        """,
                        [*params, limit],
                    )
                    return [dict(row) for row in cur.fetchall()]
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError("audit_log_unavailable", "Audit logs are unavailable", 503) from exc


