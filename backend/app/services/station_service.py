from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .air_quality import aqi_category, pm25_aqi
from .database import Database, ServiceError, dict_cursor
from .live_telemetry_engine import live_engine


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

    def _fallback_stations(self) -> list[dict[str, Any]]:
        return live_engine.get_current_stations()

    def _fallback_history(self, station_id: str, hours: int) -> dict[str, Any]:
        items = live_engine.get_history(station_id, hours=hours)
        return {"station_id": station_id, "hours": hours, "items": items}

    def _fallback_forecast_history(self, station_id: str) -> list[dict[str, Any]]:
        return live_engine.get_forecast_history(station_id)

    def list_stations(self, *, allow_fallback: bool = True) -> list[dict[str, Any]]:
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        SELECT s.station_id, s.station_name, s.location_type, s.latitude, s.longitude,
                               s.description, s.active,
                               m.pm25, m.co2, m.noise_db, m.temperature, m.measured_at AS updated_at, m.source,
                               ss.status AS explicit_status, ss.last_seen_at
                        FROM stations s
                        LEFT JOIN LATERAL (
                            SELECT station_id, pm25, co2, noise_db, temperature, measured_at, source
                            FROM measurements
                            WHERE station_id = s.station_id AND quality_flag = 'valid'
                            ORDER BY measured_at DESC
                            LIMIT 1
                        ) m ON TRUE
                        LEFT JOIN station_status ss ON ss.station_id = s.station_id
                        ORDER BY s.station_id
                        """
                    )
                    rows = cur.fetchall()
                    if not rows:
                        return self._fallback_stations() if allow_fallback else []
                    stations = [self._shape_station(row) for row in rows]
                    if allow_fallback and all(st.get("pm25") is None for st in stations):
                        return self._fallback_stations()
                    return [live_engine.apply_demo_override(station) for station in stations]
        except ServiceError as exc:
            if allow_fallback:
                return self._fallback_stations()
            raise ServiceError(
                "station_data_unavailable",
                "Station snapshots are unavailable without simulator fallback",
                503,
                {"reason_code": exc.code},
            ) from exc
        except Exception as exc:
            if allow_fallback:
                return self._fallback_stations()
            raise ServiceError(
                "station_data_unavailable",
                "Station snapshots are unavailable without simulator fallback",
                503,
            ) from exc

    def get_station(self, station_id: str) -> dict[str, Any]:
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        SELECT s.station_id, s.station_name, s.location_type, s.latitude, s.longitude,
                               s.description, s.active,
                               m.pm25, m.co2, m.noise_db, m.temperature, m.measured_at AS updated_at, m.source,
                               ss.status AS explicit_status, ss.last_seen_at
                        FROM stations s
                        LEFT JOIN LATERAL (
                            SELECT station_id, pm25, co2, noise_db, temperature, measured_at, source
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
                        found = next((s for s in self._fallback_stations() if s["station_id"] == station_id), None)
                        if not found:
                            raise ServiceError("station_not_found", "Station was not found", 404, {"station_id": station_id})
                        return found
                    station = self._shape_station(row)
                    if station.get("pm25") is None:
                        found = next((s for s in self._fallback_stations() if s["station_id"] == station_id), None)
                        return found or station
                    return live_engine.apply_demo_override(station)
        except ServiceError:
            raise
        except Exception:
            found = next((s for s in self._fallback_stations() if s["station_id"] == station_id), None)
            if not found:
                raise ServiceError("station_not_found", "Station was not found", 404, {"station_id": station_id})
            return found

    def get_history(self, station_id: str, hours: int) -> dict[str, Any]:
        try:
            self.ensure_station(station_id)
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        SELECT station_id, message_id, measured_at, received_at, pm25, co2, noise_db, temperature, humidity,
                               wind_speed, wind_direction, rainfall, source, quality_flag
                        FROM measurements
                        WHERE station_id = %s
                          AND quality_flag = 'valid'
                          AND measured_at >= NOW() - (%s || ' hours')::interval
                        ORDER BY measured_at ASC
                        """,
                        (station_id, hours),
                    )
                    rows = cur.fetchall()
                    if not rows:
                        return self._fallback_history(station_id, hours)
                    items = []
                    for row in rows:
                        item = dict(row)
                        item["aqi"] = pm25_aqi(item.get("pm25"))
                        items.append(item)
                    return {"station_id": station_id, "hours": hours, "items": items}
        except Exception:
            return self._fallback_history(station_id, hours)

    def get_forecast_history(self, station_id: str) -> list[dict[str, Any]]:
        try:
            self.ensure_station(station_id)
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        SELECT measured_at, pm25, co2, noise_db, temperature, source
                        FROM measurements
                        WHERE station_id = %s
                          AND quality_flag = 'valid'
                          AND measured_at >= NOW() - INTERVAL '90 minutes'
                        ORDER BY measured_at DESC
                        LIMIT 24
                        """,
                        (station_id,),
                    )
                    rows = cur.fetchall()
                    if not rows or len(rows) < 3:
                        return self._fallback_forecast_history(station_id)
                    history = list(reversed([dict(row) for row in rows]))
                    for item in history:
                        item["aqi"] = pm25_aqi(item.get("pm25"))
                    return history
        except Exception:
            return self._fallback_forecast_history(station_id)

    def compare_stations(self, station_ids: list[str]) -> dict[str, Any]:
        ids = list(dict.fromkeys(station_ids))
        if not ids or len(ids) > 5:
            raise ServiceError("invalid_station_ids", "Provide between 1 and 5 station ids", 422)
        try:
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
        except Exception:
            all_st = self._fallback_stations()
            rows = [st for st in all_st if st["station_id"] in ids]

        found = {row["station_id"] for row in rows}
        missing = [station_id for station_id in ids if station_id not in found]
        if missing:
            raise ServiceError("station_not_found", "One or more stations were not found", 404, {"station_id": missing})
        ranking = []
        for row in rows:
            pm = row.get("pm25")
            if pm is not None:
                ranking.append({
                    "station_id": row["station_id"],
                    "station_name": row["station_name"],
                    "pm25": pm,
                    "measured_at": row.get("measured_at") or row.get("updated_at"),
                    "source": row.get("source", "simulator"),
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
        try:
            with self.db.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM stations WHERE station_id = %s", (station_id,))
                    if not cur.fetchone():
                        raise ServiceError("station_not_found", "Station was not found", 404, {"station_id": station_id})
        except ServiceError:
            raise
        except Exception:
            if station_id not in {"S01", "S02", "S03", "S04", "S05"}:
                raise ServiceError("station_not_found", "Station was not found", 404, {"station_id": station_id})

    def _shape_station(self, row: dict[str, Any]) -> dict[str, Any]:
        last_seen = row.get("last_seen_at") or row.get("updated_at")
        status = row.get("explicit_status") or ("online" if last_seen else "offline")
        is_stale = self._is_stale(last_seen) if status == "online" else True
        effective_status = "stale" if is_stale and status == "online" else status
        pm25 = None if is_stale else row.get("pm25")
        aqi = pm25_aqi(pm25)
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
            "aqi": aqi,
            "aqi_category": aqi_category(aqi),
            "aqi_standard": "US_EPA_PM25_24H_2012",
            "co2": None if is_stale else row.get("co2"),
            "noise_db": None if is_stale else row.get("noise_db"),
            "temperature": None if is_stale else row.get("temperature"),
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
        now = datetime.now(UTC)
        return (now - last_seen.astimezone(UTC)).total_seconds() > self.stale_after_seconds
