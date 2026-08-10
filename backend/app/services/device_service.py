from __future__ import annotations

from typing import Any

from .database import Database, ServiceError, dict_cursor


class DeviceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list_devices(self) -> list[dict[str, Any]]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT device_id, device_name, device_type, station_id,
                           status, is_simulated, last_seen_at
                    FROM devices
                    ORDER BY device_id
                    """
                )
                return [dict(row) for row in cur.fetchall()]

    def get_status(self, device_id: str) -> dict[str, Any]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT device_id, device_name, device_type, station_id,
                           status, is_simulated, last_seen_at
                    FROM devices
                    WHERE device_id = %s
                    """,
                    (device_id,),
                )
                row = cur.fetchone()
        if not row:
            raise ServiceError("device_not_found", "Device was not found", 404, {"device_id": device_id})
        return dict(row)
