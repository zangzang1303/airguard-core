from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import psycopg2
import psycopg2.extras

from .schemas import DeviceStatusPayload, MeasurementPayload, StationStatusPayload
from .validator import ValidationErrorCode

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PersistResult:
    accepted: bool
    duplicate: bool = False
    measurement_id: int | None = None


class PostgresStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self):
        conn = psycopg2.connect(self.database_url)
        conn.set_client_encoding("UTF8")
        return conn

    def persist_measurement(self, payload: MeasurementPayload) -> PersistResult:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO measurements (
                        message_id, station_id, measured_at, pm25, co2, noise_db, temperature, humidity,
                        wind_speed, wind_direction, rainfall, source, quality_flag, received_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'valid', NOW())
                    ON CONFLICT (message_id) DO NOTHING
                    RETURNING measurement_id
                    """,
                    (
                        payload.message_id,
                        payload.station_id,
                        payload.timestamp,
                        payload.pm25,
                        payload.co2,
                        payload.noise_db,
                        payload.temperature,
                        payload.humidity,
                        payload.wind_speed,
                        payload.wind_direction,
                        payload.rainfall,
                        payload.source,
                    ),
                )
                inserted = cur.fetchone()
                if not inserted:
                    self.record_rejection(
                        topic=f"airguard/stations/{payload.station_id}/measurements",
                        station_id=payload.station_id,
                        message_id=payload.message_id,
                        reason=ValidationErrorCode.DUPLICATE,
                        detail="duplicate message_id",
                        payload={"message_id": payload.message_id, "station_id": payload.station_id},
                        conn=conn,
                    )
                    return PersistResult(accepted=False, duplicate=True)

                self._upsert_station_status(
                    cur,
                    station_id=payload.station_id,
                    status="online",
                    observed_at=payload.timestamp,
                    source=payload.source,
                    reason=None,
                )
                return PersistResult(accepted=True, measurement_id=inserted["measurement_id"])

    def persist_status(self, payload: StationStatusPayload) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                self._upsert_station_status(
                    cur,
                    station_id=payload.station_id,
                    status=payload.status,
                    observed_at=payload.timestamp,
                    source=payload.source,
                    reason=payload.reason,
                )

    def persist_device_status(self, payload: DeviceStatusPayload) -> bool:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT command_intent_id, approval_request_id, status,
                           acknowledged_at, ack_status, device_state, dispatch_error
                    FROM device_command_intents
                    WHERE command_id = %s AND device_id = %s
                    LIMIT 1
                    """,
                    (payload.command_id, payload.device_id),
                )
                dispatch = cur.fetchone()
                approval_request_id = str(dispatch["approval_request_id"]) if dispatch and dispatch.get("approval_request_id") else None
                command_intent_id = str(dispatch["command_intent_id"]) if dispatch else None
                if dispatch:
                    acknowledged_at = dispatch.get("acknowledged_at")
                    is_newer = acknowledged_at is None or payload.timestamp >= acknowledged_at
                    preserves_success = dispatch.get("status") == "succeeded" and payload.status != "succeeded"
                    should_apply = is_newer and not preserves_success
                    if should_apply:
                        effective_status = payload.status
                        effective_acknowledged_at = payload.timestamp
                        effective_ack_status = payload.status
                        effective_device_state = payload.device_state or dispatch.get("device_state")
                        effective_error = (
                            payload.reason
                            if payload.status in {"failed", "rejected"}
                            else dispatch.get("dispatch_error")
                        )
                        cur.execute(
                            """
                            UPDATE devices
                            SET status = %s, last_seen_at = %s, is_simulated = TRUE
                            WHERE device_id = %s
                              AND (last_seen_at IS NULL OR %s >= last_seen_at)
                            """,
                            (
                                payload.device_state or payload.status,
                                payload.timestamp,
                                payload.device_id,
                                payload.timestamp,
                            ),
                        )
                    else:
                        effective_status = dispatch["status"]
                        effective_acknowledged_at = acknowledged_at
                        effective_ack_status = dispatch.get("ack_status")
                        effective_device_state = dispatch.get("device_state")
                        effective_error = dispatch.get("dispatch_error")
                    cur.execute(
                        """
                        UPDATE device_command_intents
                        SET status = %s, acknowledged_at = %s, ack_status = %s,
                            device_state = %s, dispatch_error = %s
                        WHERE command_intent_id = %s
                        """,
                        (
                            effective_status,
                            effective_acknowledged_at,
                            effective_ack_status,
                            effective_device_state,
                            effective_error,
                            command_intent_id,
                        ),
                    )
                else:
                    cur.execute(
                        "SELECT device_id FROM devices WHERE device_id = %s",
                        (payload.device_id,),
                    )
                    if cur.fetchone() is None:
                        return False

                cur.execute(
                    """
                    INSERT INTO device_status_events (
                        command_id, command_intent_id, device_id, status,
                        device_state, reason, observed_at, is_simulated
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (device_id, command_id, status) DO NOTHING
                    """,
                    (
                        payload.command_id,
                        command_intent_id,
                        payload.device_id,
                        payload.status,
                        payload.device_state,
                        payload.reason,
                        payload.timestamp,
                        payload.is_simulated,
                    ),
                )

                action = "device_command.ack" if approval_request_id else "device_command.ack.unmatched"
                cur.execute(
                    """
                    INSERT INTO audit_logs (
                        actor_type, actor_id, actor_role, action, entity_type,
                        entity_id, outcome, correlation_id, details
                    )
                    VALUES ('device', %s, 'simulator', %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        payload.device_id,
                        action,
                        "approval_request" if approval_request_id else "device",
                        approval_request_id or payload.device_id,
                        "success" if payload.status in {"succeeded", "duplicate"} else "failure",
                        payload.command_id,
                        json.dumps(
                            {
                                "command_id": payload.command_id,
                                "device_id": payload.device_id,
                                "ack_status": payload.status,
                                "device_state": payload.device_state,
                                "reason": payload.reason,
                                "is_simulated": payload.is_simulated,
                                "observed_at": payload.timestamp.isoformat(),
                            },
                            ensure_ascii=True,
                        ),
                    ),
                )
                return True

    def record_rejection(
        self,
        *,
        topic: str,
        station_id: str | None,
        message_id: str | None,
        reason: ValidationErrorCode | str,
        detail: str | None,
        payload: dict[str, Any] | None,
        conn=None,
    ) -> None:
        owns_conn = conn is None
        if conn is None:
            conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO mqtt_rejections (topic, station_id, message_id, reason, detail, payload_excerpt)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        topic,
                        station_id,
                        message_id,
                        str(reason),
                        detail,
                        json.dumps(payload or {}, ensure_ascii=True)[:2000],
                    ),
                )
            if owns_conn:
                conn.commit()
        except Exception:
            logger.exception("failed to record mqtt rejection")
            if owns_conn:
                conn.rollback()
        finally:
            if owns_conn:
                conn.close()

    @staticmethod
    def _upsert_station_status(cur, *, station_id: str, status: str, observed_at, source: str, reason: str | None) -> None:
        cur.execute(
            """
            INSERT INTO station_status (station_id, status, last_seen_at, source, reason, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (station_id) DO UPDATE SET
                status = EXCLUDED.status,
                last_seen_at = GREATEST(COALESCE(station_status.last_seen_at, EXCLUDED.last_seen_at), EXCLUDED.last_seen_at),
                source = EXCLUDED.source,
                reason = EXCLUDED.reason,
                updated_at = NOW()
            WHERE station_status.last_seen_at IS NULL
               OR EXCLUDED.last_seen_at >= station_status.last_seen_at
            """,
            (station_id, status, observed_at, source, reason),
        )



