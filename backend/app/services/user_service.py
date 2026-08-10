from __future__ import annotations

from typing import Any

from .database import Database, ServiceError, dict_cursor


class UserService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_profile(self, user_id: str) -> dict[str, Any]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    "SELECT user_id, role, sensitivity_group FROM users WHERE user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
        if not row:
            raise ServiceError("user_not_found", "User profile was not found", 404, {"user_id": user_id})
        return dict(row)
