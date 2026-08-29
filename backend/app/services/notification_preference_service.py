from __future__ import annotations

from typing import Any


class NotificationPreferenceService:
    def __init__(self, repository: Any, audit_service: Any) -> None:
        self.repository = repository
        self.audit = audit_service

    def get(self, user_id: str) -> dict[str, bool]:
        return self.repository.get_preferences(user_id)

    def update(
        self,
        *,
        user_id: str,
        actor_role: str,
        values: dict[str, bool],
        correlation_id: str,
    ) -> dict[str, bool]:
        before = self.repository.get_preferences(user_id)
        updated = self.repository.update_preferences(user_id, values)
        changed_fields = sorted(key for key, value in updated.items() if before.get(key) != value)
        self.audit.record(
            actor_type="user",
            actor_id=user_id,
            actor_role=actor_role,
            action="auth.notification_preferences_updated",
            entity_type="user",
            entity_id=user_id,
            correlation_id=correlation_id,
            details={"changed_fields": changed_fields},
        )
        return updated
