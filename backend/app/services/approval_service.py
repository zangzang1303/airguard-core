from __future__ import annotations

import os

import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://airguard:airguard@localhost:5432/airguard")


class ApprovalStoreUnavailableError(ConnectionError):
    pass


def require_approved_device_action(request_id: str, device_id: str, command: str) -> bool:
    try:
        with psycopg2.connect(DATABASE_URL, connect_timeout=2) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM approval_requests
                WHERE request_id::text = %s
                  AND device_id = %s
                  AND proposed_action = %s
                  AND status = 'approved'
                """,
                (request_id, device_id, command),
            )
            return cursor.fetchone() is not None
    except psycopg2.Error as exc:
        raise ApprovalStoreUnavailableError("PostgreSQL approval check is temporarily unavailable") from exc
