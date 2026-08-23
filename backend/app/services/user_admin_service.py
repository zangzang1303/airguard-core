from __future__ import annotations

from typing import Any

from .audit_service import AuditService
from .database import Database, ServiceError, dict_cursor


class UserAdminService:
    """Transactional administrator mutations for user role and account status."""

    _ROLES = {"resident", "manager", "admin"}
    _STATUSES = {"active", "disabled"}

    def __init__(self, db: Database, audit: AuditService) -> None:
        self.db = db
        self.audit = audit

    def list_users(self) -> list[dict[str, Any]]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT u.user_id, u.email, u.role, u.full_name, u.sensitivity_group,
                           u.email_verified_at, u.is_active, u.created_at, u.updated_at,
                           MAX(s.last_seen_at) AS last_active_at
                    FROM users u
                    LEFT JOIN user_sessions s ON s.user_id = u.user_id
                    GROUP BY u.user_id
                    ORDER BY u.created_at DESC
                    """
                )
                return [self._serialize(dict(row)) for row in cur.fetchall()]

    def update_user(
        self,
        *,
        target_user_id: str,
        actor_user_id: str,
        actor_role: str,
        role: str | None,
        status: str | None,
        reason: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        if role is None and status is None:
            raise ServiceError("empty_user_update", "Role or status is required", 422)
        if role is not None and role not in self._ROLES:
            raise ServiceError("invalid_user_role", "Unsupported user role", 422)
        if status is not None and status not in self._STATUSES:
            raise ServiceError("invalid_user_status", "Unsupported user status", 422)
        if not reason.strip():
            raise ServiceError("user_update_reason_required", "A reason is required", 422)
        if target_user_id == actor_user_id:
            raise ServiceError("self_admin_mutation_forbidden", "Administrators cannot change their own role or status", 409)

        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, role, full_name, sensitivity_group,
                           email_verified_at, is_active, created_at, updated_at
                    FROM users
                    WHERE user_id = %s
                    FOR UPDATE
                    """,
                    (target_user_id,),
                )
                current = cur.fetchone()
                if not current:
                    raise ServiceError("user_not_found", "User account was not found", 404)
                current = dict(current)

                removes_active_admin = (
                    current["role"] == "admin"
                    and current["is_active"]
                    and (role not in {None, "admin"} or status == "disabled")
                )
                if removes_active_admin:
                    cur.execute(
                        "SELECT COUNT(*) AS count FROM users WHERE role = 'admin' AND is_active = TRUE AND user_id <> %s",
                        (target_user_id,),
                    )
                    if int(cur.fetchone()["count"]) == 0:
                        raise ServiceError("last_admin_protected", "The last active administrator cannot be removed", 409)

                new_active = None if status is None else status == "active"
                cur.execute(
                    """
                    UPDATE users
                    SET role = COALESCE(%s, role),
                        is_active = COALESCE(%s, is_active),
                        updated_at = NOW()
                    WHERE user_id = %s
                    RETURNING user_id, email, role, full_name, sensitivity_group,
                              email_verified_at, is_active, created_at, updated_at
                    """,
                    (role, new_active, target_user_id),
                )
                updated = dict(cur.fetchone())
                if status == "disabled":
                    cur.execute(
                        "UPDATE user_sessions SET revoked_at = NOW() WHERE user_id = %s AND revoked_at IS NULL",
                        (target_user_id,),
                    )

                action = "user.admin_updated"
                audit_row = self.audit.record(
                    actor_type="user",
                    actor_id=actor_user_id,
                    actor_role=actor_role,
                    action=action,
                    entity_type="user",
                    entity_id=target_user_id,
                    correlation_id=correlation_id,
                    details={
                        "reason": reason.strip(),
                        "previous_role": current["role"],
                        "new_role": updated["role"],
                        "previous_status": "active" if current["is_active"] else "disabled",
                        "new_status": "active" if updated["is_active"] else "disabled",
                    },
                    conn=conn,
                )
                return {
                    "user": self._serialize(updated),
                    "audit": {
                        "audit_id": audit_row["audit_id"],
                        "created_at": audit_row["created_at"],
                        "actor_id": actor_user_id,
                        "actor_role": actor_role,
                        "action": action,
                        "entity_type": "user",
                        "entity_id": target_user_id,
                        "outcome": "success",
                        "correlation_id": correlation_id,
                        "details": {"reason": reason.strip()},
                    },
                }

    @staticmethod
    def _serialize(row: dict[str, Any]) -> dict[str, Any]:
        serialized = dict(row)
        sensitivity_group = serialized.pop("sensitivity_group", None)
        is_active = bool(serialized.pop("is_active", False))
        return {
            **serialized,
            "user_id": str(row["user_id"]),
            "user_group": sensitivity_group or "normal",
            "status": "active" if is_active else "disabled",
            "full_name": row.get("full_name") or row.get("email") or "AirGuard user",
        }
