from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import psycopg2
import psycopg2.extras

from .schemas import MeasurementPayload, StationStatusPayload
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
        return psycopg2.connect(self.database_url)

    def persist_measurement(self, payload: MeasurementPayload) -> PersistResult:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO measurements (
                        message_id, station_id, measured_at, pm25, temperature, humidity,
                        wind_speed, wind_direction, rainfall, source, quality_flag
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'valid')
                    ON CONFLICT (message_id) DO NOTHING
                    RETURNING measurement_id
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



