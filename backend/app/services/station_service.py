from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .database import Database, ServiceError, dict_cursor


def pm25_level(pm25: float | None) -> str | None:
    if pm25 is None:
        return None
    if pm25 <= 25:
        return "good"
    if pm25 <= 50:
        return "moderate"
    if pm25 <= 100:
        return "unhealthy"
    return "very_unhealthy"


class StationService:
    def __init__(self, db: Database, stale_after_seconds: int) -> None:
        self.db = db
        self.stale_after_seconds = stale_after_seconds

    def list_stations(self) -> list[dict[str, Any]]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT s.station_id, s.station_name, s.location_type, s.latitude, s.longitude,
                           s.description, s.active,
                           m.pm25, m.measured_at AS updated_at, m.source,
                           ss.status AS explicit_status, ss.last_seen_at
                    FROM stations s
                    LEFT JOIN LATERAL (
                        SELECT station_id, pm25, measured_at, source
                        FROM measurements
                        WHERE station_id = s.station_id AND quality_flag = 'valid'
                        ORDER BY measured_at DESC
                        LIMIT 1
                    ) m ON TRUE
                    LEFT JOIN station_status ss ON ss.station_id = s.station_id
                    ORDER BY s.station_id
                    """
                )
                return [self._shape_station(row) for row in cur.fetchall()]

    def get_station(self, station_id: str) -> dict[str, Any]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT s.station_id, s.station_name, s.location_type, s.latitude, s.longitude,
                           s.description, s.active,
                           m.pm25, m.measured_at AS updated_at, m.source,
                           ss.status AS explicit_status, ss.last_seen_at
                    FROM stations s
                    LEFT JOIN LATERAL (
                        SELECT station_id, pm25, measured_at, source
                        FROM measurements
                        WHERE station_id = s.station_id AND quality_flag = 'valid'
                        ORDER BY measured_at DESC
                        LIMIT 1
                    ) m ON TRUE
                    LEFT JOIN station_status ss ON ss.station_id = s.station_id
                    WHERE s.station_id = %s
                    """,
                    (station_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ServiceError("station_not_found", "Station was not found", 404, {"station_id": station_id})
                return self._shape_station(row)

    def get_history(self, station_id: str, hours: int) -> dict[str, Any]:
        self.ensure_station(station_id)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT station_id, message_id, measured_at, received_at, pm25, temperature, humidity,
                           wind_speed, wind_direction, rainfall, source, quality_flag
                    FROM measurements
                    WHERE station_id = %s
                      AND quality_flag = 'valid'
                      AND measured_at >= NOW() - (%s || ' hours')::interval
                    ORDER BY measured_at ASC
                    """,
                    (station_id, hours),
                )
                return {"station_id": station_id, "hours": hours, "items": [dict(row) for row in cur.fetchall()]}

    def compare_stations(self, station_ids: list[str]) -> dict[str, Any]:
        """Return only current, valid and fresh measurements for requested stations."""
        ids = list(dict.fromkeys(station_ids))
        if not ids or len(ids) > 5:
            raise ServiceError("invalid_station_ids", "Provide between 1 and 5 station ids", 422)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT s.station_id, s.station_name, m.pm25, m.measured_at, m.source,
                           ss.status AS explicit_status, ss.last_seen_at
                    FROM stations s
                    LEFT JOIN LATERAL (
                        SELECT pm25, measured_at, source
                        FROM measurements
                        WHERE station_id = s.station_id AND quality_flag = 'valid'
                        ORDER BY measured_at DESC LIMIT 1
                    ) m ON TRUE
                    LEFT JOIN station_status ss ON ss.station_id = s.station_id
                    WHERE s.station_id = ANY(%s)
                    """,
                    (ids,),
                )
                rows = cur.fetchall()
        found = {row["station_id"] for row in rows}
        missing = [station_id for station_id in ids if station_id not in found]
        if missing:
            raise ServiceError("station_not_found", "One or more stations were not found", 404, {"station_ids": missing})
        ranking = []
        for row in rows:
            last_seen = row.get("last_seen_at") or row.get("measured_at")
            status = row.get("explicit_status") or ("online" if last_seen else "offline")
            fresh = status == "online" and not self._is_stale(last_seen) and row.get("pm25") is not None
            if fresh:
                ranking.append({
                    "station_id": row["station_id"],
                    "station_name": row["station_name"],
                    "pm25": row["pm25"],
                    "measured_at": row["measured_at"],
                    "source": row["source"],
                    "status": "online",
                })
        ranking.sort(key=lambda item: item["pm25"], reverse=True)
        for index, item in enumerate(ranking, start=1):
            item["rank"] = index
        return {
            "ranking": ranking,
            "best_station_id": ranking[-1]["station_id"] if ranking else None,
            "worst_station_id": ranking[0]["station_id"] if ranking else None,
            "comparison_valid": bool(ranking),
            "requested_station_ids": ids,
        }

    def ensure_station(self, station_id: str) -> None:
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM stations WHERE station_id = %s", (station_id,))
                if not cur.fetchone():
                    raise ServiceError("station_not_found", "Station was not found", 404, {"station_id": station_id})

    def _shape_station(self, row: dict[str, Any]) -> dict[str, Any]:
        last_seen = row.get("last_seen_at") or row.get("updated_at")
        status = row.get("explicit_status") or ("online" if last_seen else "offline")
        is_stale = self._is_stale(last_seen) if status == "online" else True
        effective_status = "stale" if is_stale and status == "online" else status
        pm25 = None if is_stale else row.get("pm25")
        freshness = "fresh" if pm25 is not None and not is_stale and effective_status == "online" else (
            "stale" if is_stale else "unavailable"
        )
        return {
            "station_id": row["station_id"],
            "station_name": row["station_name"],
            "location_type": row["location_type"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "description": row.get("description"),
            "active": row.get("active", True),
            "pm25": pm25,
            "level": pm25_level(pm25),
            "status": effective_status,
            "is_stale": is_stale,
            "freshness": freshness,
            "updated_at": row.get("updated_at") or last_seen,
            "last_seen_at": last_seen,
            "source": row.get("source") if pm25 is not None else None,
        }

    def _is_stale(self, last_seen: datetime | None) -> bool:
        if not last_seen:
            return True
        now = datetime.now(timezone.utc)
        return (now - last_seen.astimezone(timezone.utc)).total_seconds() > self.stale_after_seconds
