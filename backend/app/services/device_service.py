from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from .audit_service import AuditService
from .database import Database, ServiceError, dict_cursor


class DeviceService:
    def __init__(self, db: Database, audit_service: AuditService | None = None) -> None:
        self.db = db
        self.audit_service = audit_service

    def list_devices(self) -> list[dict[str, Any]]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT d.device_id, d.device_name, d.device_type, d.station_id,
                           d.status, d.is_simulated, d.last_seen_at,
                           s.station_name, s.latitude, s.longitude,
                           intent.command_intent_id, intent.approval_request_id,
                           intent.command, intent.status AS command_status,
                           intent.duration_minutes, intent.intensity_percent,
                           intent.command_id, intent.created_at AS command_created_at,
                           intent.dispatched_at, intent.acknowledged_at,
                           intent.ack_status, intent.device_state,
                           approval.reviewed_by, approval.reviewed_at,
                           approval.review_note,
                           reviewer.full_name AS reviewer_name
                    FROM devices AS d
                    LEFT JOIN stations AS s ON s.station_id = d.station_id
                    LEFT JOIN LATERAL (
                        SELECT *
                        FROM device_command_intents
                        WHERE device_id = d.device_id
                        ORDER BY created_at DESC
                        LIMIT 1
                    ) AS intent ON TRUE
                    LEFT JOIN approval_requests AS approval
                      ON approval.request_id = intent.approval_request_id
                    LEFT JOIN users AS reviewer
                      ON reviewer.user_id = approval.reviewed_by
                    ORDER BY d.device_id
                    """
                )
                return [self._shape_device(dict(row), cur) for row in cur.fetchall()]

    def list_ventilation_devices(self, *, station_id: str | None = None) -> list[dict[str, Any]]:
        devices = self.list_devices()
        if station_id is None:
            return devices
        return [item for item in devices if item.get("station_id") == station_id]

    def get_status(self, device_id: str) -> dict[str, Any]:
        row = next((item for item in self.list_devices() if item["device_id"] == device_id), None)
        if row is None:
            raise ServiceError("device_not_found", "Device was not found", 404, {"device_id": device_id})
        return row

    def _shape_device(self, row: dict[str, Any], cur: Any) -> dict[str, Any]:
        now = datetime.now(UTC)
        started_at = row.get("acknowledged_at")
        duration_minutes = row.get("duration_minutes")
        ends_at: datetime | None = None
        if started_at and duration_minutes:
            ends_at = started_at.astimezone(UTC) + timedelta(minutes=int(duration_minutes))

        raw_mode = str(row.get("device_state") or row.get("status") or "STANDBY").upper()
        if raw_mode in {"OFFLINE", "SUCCEEDED", "PUBLISHED", "QUEUED", "PUBLISHING"}:
            raw_mode = "STANDBY"
        if ends_at and ends_at <= now and raw_mode in {"RUNNING_BOOST", "AIR_PURIFIER_ON"}:
            raw_mode = "STANDBY"

        remaining_seconds = (
            max(0, int((ends_at - now).total_seconds()))
            if ends_at and raw_mode in {"RUNNING_BOOST", "AIR_PURIFIER_ON"}
            else 0
        )
        effectiveness = self._effectiveness(cur, row)
        latest_command = None
        if row.get("command_intent_id"):
            latest_command = {
                "command_intent_id": str(row["command_intent_id"]),
                "approval_request_id": str(row["approval_request_id"]) if row.get("approval_request_id") else None,
                "command_id": row.get("command_id"),
                "action": row.get("command"),
                "status": row.get("command_status"),
                "ack_status": row.get("ack_status"),
                "approved_by": row.get("reviewed_by"),
                "approved_by_name": row.get("reviewer_name"),
                "approved_at": row.get("reviewed_at"),
                "review_note": row.get("review_note"),
            }

        return {
            "device_id": row["device_id"],
            "device_name": row["device_name"],
            "device_type": row["device_type"],
            "station_id": row.get("station_id"),
            "station_name": row.get("station_name"),
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "status": row.get("status"),
            "operating_mode": raw_mode,
            "is_active": raw_mode in {"RUNNING_BOOST", "AIR_PURIFIER_ON"} and remaining_seconds > 0,
            "is_simulated": bool(row.get("is_simulated")),
            "last_seen_at": row.get("last_seen_at"),
            "started_at": started_at,
            "ends_at": ends_at,
            "duration_minutes": duration_minutes,
            "intensity_percent": row.get("intensity_percent"),
            "remaining_seconds": remaining_seconds,
            "effectiveness": effectiveness,
            "latest_command": latest_command,
            "source": "simulator",
        }

    def create_manual_command_intent(
        self,
        *,
        device_id: str,
        station_id: str,
        action: str,
        actor_id: str,
        actor_role: str,
        idempotency_key: str,
        duration_minutes: int | None,
        intensity_percent: int | None,
        correlation_id: str | None,
    ) -> dict[str, Any]:
        """Persist a Manager's direct simulated-device command without an approval request."""
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT command_intent_id, device_id, station_id, command,
                           duration_minutes, intensity_percent, status, idempotency_key
                    FROM device_command_intents
                    WHERE idempotency_key = %s
                    """,
                    (idempotency_key,),
                )
                existing = cur.fetchone()
                if existing:
                    return {**dict(existing), "reused": True}
                command_intent_id = str(uuid4())
                cur.execute(
                    """
                    INSERT INTO device_command_intents (
                        command_intent_id, approval_request_id, device_id, station_id,
                        command, duration_minutes, intensity_percent, status, idempotency_key
                    )
                    VALUES (%s, NULL, %s, %s, %s, %s, %s, 'queued', %s)
                    RETURNING command_intent_id, device_id, station_id, command,
                              duration_minutes, intensity_percent, status, idempotency_key
                    """,
                    (
                        command_intent_id,
                        device_id,
                        station_id,
                        action,
                        duration_minutes,
                        intensity_percent,
                        idempotency_key,
                    ),
                )
                intent = dict(cur.fetchone())
                if self.audit_service:
                    self.audit_service.record(
                        actor_type="user",
                        actor_id=actor_id,
                        actor_role=actor_role,
                        action="device.manual_control",
                        entity_type="device",
                        entity_id=device_id,
                        correlation_id=correlation_id,
                        details={
                            "command_intent_id": command_intent_id,
                            "station_id": station_id,
                            "action": action,
                        },
                        conn=conn,
                    )
                return intent

    def get_manual_command_intent(
        self,
        *,
        command_intent_id: str,
        device_id: str,
        command: str,
    ) -> dict[str, Any] | None:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT command_intent_id, device_id, station_id, command,
                           duration_minutes, intensity_percent, status, idempotency_key,
                           command_id, ack_status
                    FROM device_command_intents
                    WHERE command_intent_id = %s
                      AND approval_request_id IS NULL
                      AND device_id = %s
                      AND command = %s
                    """,
                    (command_intent_id, device_id, command),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def record_manual_dispatch(
        self,
        *,
        command_intent_id: str,
        status: str,
        command_id: str | None,
        error: str | None,
        correlation_id: str | None,
    ) -> None:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE device_command_intents
                    SET status = CASE WHEN status = 'succeeded' OR ack_status = 'succeeded' THEN status ELSE %s END,
                        dispatched_at = CASE WHEN status = 'succeeded' OR ack_status = 'succeeded' THEN dispatched_at ELSE NOW() END,
                        dispatch_error = CASE WHEN status = 'succeeded' OR ack_status = 'succeeded' THEN dispatch_error ELSE %s END,
                        command_id = COALESCE(command_id, %s)
                    WHERE command_intent_id = %s
                    """,
                    (status, error, command_id, command_intent_id),
                )
            if self.audit_service:
                self.audit_service.record(
                    actor_type="system",
                    actor_role="backend",
                    action={
                        "publishing": "device_command.dispatch.prepare",
                        "published": "device_command.dispatch",
                    }.get(status, "device_command.dispatch.failure"),
                    entity_type="device_command",
                    entity_id=command_intent_id,
                    correlation_id=correlation_id,
                    outcome="success" if status in {"publishing", "published"} else "failure",
                    details={"status": status, "error": error, "command_id": command_id},
                    conn=conn,
                )

    @staticmethod
    def _effectiveness(cur: Any, row: dict[str, Any]) -> dict[str, Any] | None:
        station_id = row.get("station_id")
        started_at = row.get("acknowledged_at")
        if not station_id or not started_at:
            return None
        cur.execute(
            """
            SELECT
              (SELECT pm25 FROM measurements
               WHERE station_id = %s AND quality_flag = 'valid' AND measured_at <= %s
               ORDER BY measured_at DESC LIMIT 1) AS baseline_pm25,
              (SELECT co2 FROM measurements
               WHERE station_id = %s AND quality_flag = 'valid' AND measured_at <= %s
               ORDER BY measured_at DESC LIMIT 1) AS baseline_co2,
              (SELECT pm25 FROM measurements
               WHERE station_id = %s AND quality_flag = 'valid'
               ORDER BY measured_at DESC LIMIT 1) AS current_pm25,
              (SELECT co2 FROM measurements
               WHERE station_id = %s AND quality_flag = 'valid'
               ORDER BY measured_at DESC LIMIT 1) AS current_co2,
              (SELECT measured_at FROM measurements
               WHERE station_id = %s AND quality_flag = 'valid'
               ORDER BY measured_at DESC LIMIT 1) AS measured_at
            """,
            (
                station_id,
                started_at,
                station_id,
                started_at,
                station_id,
                station_id,
                station_id,
            ),
        )
        measurement = cur.fetchone()
        if not measurement:
            return None
        data = dict(measurement)
        baseline_pm25 = data.get("baseline_pm25")
        current_pm25 = data.get("current_pm25")
        baseline_co2 = data.get("baseline_co2")
        current_co2 = data.get("current_co2")

        def reduction_percent(initial: Any, current: Any) -> float | None:
            if initial is None or current is None or float(initial) <= 0:
                return None
            return round((float(initial) - float(current)) / float(initial) * 100, 1)

        return {
            "baseline_pm25": baseline_pm25,
            "current_pm25": current_pm25,
            "pm25_reduction_percent": reduction_percent(baseline_pm25, current_pm25),
            "baseline_co2": baseline_co2,
            "current_co2": current_co2,
            "co2_reduction_percent": reduction_percent(baseline_co2, current_co2),
            "measured_at": data.get("measured_at"),
        }
