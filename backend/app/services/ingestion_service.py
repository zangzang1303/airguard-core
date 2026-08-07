from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..schemas.measurements import MeasurementIngestionRequest

from .audit_service import AuditService
from .database import Database, ServiceError, dict_cursor


class MeasurementIngestionService:
    def __init__(self, db: Database, *, stale_after_seconds: int, max_future_skew_seconds: int = 60, audit_service: AuditService | None = None) -> None:
        self.db = db
        self.stale_after_seconds = stale_after_seconds
        self.max_future_skew_seconds = max_future_skew_seconds
        self.audit_service = audit_service

    def ingest(self, payload: MeasurementIngestionRequest) -> dict[str, Any]:
        self._validate_freshness(payload.timestamp)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute("SELECT 1 FROM stations WHERE station_id = %s", (payload.station_id,))
                if not cur.fetchone():
                    raise ServiceError("unknown_station", "Station is not registered", 404, {"station_id": payload.station_id})

                cur.execute(
                    """
                    INSERT INTO measurements (
                        message_id, station_id, measured_at, pm25, temperature, humidity,
                        wind_speed, wind_direction, rainfall, source, quality_flag
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'valid')
                    ON CONFLICT (message_id) DO NOTHING
                    RETURNING measurement_id, message_id, station_id, measured_at, pm25, source
                    """,
                    (
                        payload.message_id,
                        payload.station_id,
                        payload.timestamp,
                        payload.pm25,
                        payload.temperature,
                        payload.humidity,
                        payload.wind_speed,
                        payload.wind_direction,
                        payload.rainfall,
                        payload.source,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    return {"accepted": False, "duplicate": True, "message_id": payload.message_id, "reason": "duplicate"}

                cur.execute(
                    """
                    INSERT INTO station_status (station_id, status, last_seen_at, source, reason, updated_at)
                    VALUES (%s, 'online', %s, %s, NULL, NOW())
                    ON CONFLICT (station_id) DO UPDATE SET
                        status = 'online',
                        last_seen_at = GREATEST(COALESCE(station_status.last_seen_at, EXCLUDED.last_seen_at), EXCLUDED.last_seen_at),
                        source = EXCLUDED.source,
                        reason = NULL,
                        updated_at = NOW()
                    WHERE station_status.last_seen_at IS NULL
                       OR EXCLUDED.last_seen_at >= station_status.last_seen_at
                    """,
                    (payload.station_id, payload.timestamp, payload.source),
                )
                if self.audit_service is not None:
                    self.audit_service.record(
                        actor_type="system",
                        action="measurement.accepted",
                        entity_type="measurement",
                        entity_id=str(row["measurement_id"]),
                        details={
                            "station_id": payload.station_id,
                            "message_id": payload.message_id,
                            "source": payload.source,
                        },
                        conn=conn,
                    )
                return {"accepted": True, "duplicate": False, "measurement": dict(row)}

    def _validate_freshness(self, timestamp: datetime) -> None:
        now = datetime.now(timezone.utc)
        event_time = timestamp.astimezone(timezone.utc)
        age = (now - event_time).total_seconds()
        if age < -self.max_future_skew_seconds:
            raise ServiceError("future_time", "Measurement timestamp is too far in the future", 422)
        if age > self.stale_after_seconds:
            raise ServiceError("stale", "Measurement timestamp is older than stale threshold", 422)
