from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from .database import Database, ServiceError, dict_cursor
from .air_quality import aqi_category, pm25_aqi


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
        now_iso = datetime.now(timezone.utc).isoformat()
        seeds = [
            {"station_id": "S01", "station_name": "Trục Đa Tốn phía Tây Bắc", "location_type": "northwest_road", "latitude": 21.0008, "longitude": 105.9428, "pm25": 42.5, "co2": 650, "noise_db": 57, "temperature": 31.1},
            {"station_id": "S02", "Khu căn hộ Sapphire": "Khu căn hộ Sapphire", "station_name": "Khu căn hộ Sapphire", "location_type": "high_rise_residential", "latitude": 20.9975, "longitude": 105.9430, "pm25": 55.2, "co2": 720, "noise_db": 65, "temperature": 31.8},
            {"station_id": "S03", "station_name": "Ven Hồ Ngọc Trai", "location_type": "lakeside_residential", "latitude": 20.9953, "longitude": 105.9500, "pm25": 66.1, "co2": 780, "noise_db": 71, "temperature": 32.4},
            {"station_id": "S04", "station_name": "Khuôn viên VinUni", "location_type": "university_campus", "latitude": 20.9898, "longitude": 105.9467, "pm25": 28.4, "co2": 540, "noise_db": 49, "temperature": 30.2},
            {"station_id": "S05", "station_name": "Khu Hải Âu phía Đông Nam", "location_type": "southeast_residential", "latitude": 20.9910, "longitude": 105.9560, "pm25": 35.9, "co2": 590, "noise_db": 54, "temperature": 30.8},
        ]
        result = []
        for s in seeds:
            aqi = pm25_aqi(s["pm25"])
            result.append({
                "station_id": s["station_id"],
                "station_name": s["station_name"],
                "location_type": s["location_type"],
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "description": f"Trạm quan trắc {s['station_name']}",
                "active": True,
                "pm25": s["pm25"],
                "aqi": aqi,
                "aqi_category": aqi_category(aqi),
                "aqi_standard": "US_EPA_PM25_24H_2012",
                "co2": s["co2"],
                "noise_db": s["noise_db"],
                "temperature": s["temperature"],
                "level": pm25_level(s["pm25"]),
                "status": "online",
                "is_stale": False,
                "freshness": "fresh",
                "updated_at": now_iso,
                "last_seen_at": now_iso,
                "source": "simulator",
            })
        return result

    def _fallback_history(self, station_id: str, hours: int) -> dict[str, Any]:
        st = next((s for s in self._fallback_stations() if s["station_id"] == station_id), None)
        base_pm = st["pm25"] if st else 40.0
        now = datetime.now(timezone.utc)
        items = []
        for i in range(hours, 0, -1):
            t = now - timedelta(hours=i)
            pm = round(base_pm + (i % 5 - 2) * 2.5, 1)
            items.append({
                "station_id": station_id,
                "message_id": f"HIST-{station_id}-{i}",
                "measured_at": t.isoformat(),
                "received_at": t.isoformat(),
                "timestamp": t.isoformat(),
                "pm25": pm,
                "aqi": pm25_aqi(pm),
                "co2": 600 + i * 5,
                "noise_db": 55 + (i % 4),
                "temperature": 30.0 + (i % 3),
                "humidity": 65,
                "source": "simulator",
                "quality_flag": "valid",
            })
        return {"station_id": station_id, "hours": hours, "items": items}

    def _fallback_forecast_history(self, station_id: str) -> list[dict[str, Any]]:
        st = next((s for s in self._fallback_stations() if s["station_id"] == station_id), None)
        base_pm = st["pm25"] if st else 40.0
        now = datetime.now(timezone.utc)
        history = []
        for i in range(12, 0, -1):
            t = now - timedelta(minutes=i * 5)
            pm = round(base_pm + (i % 3 - 1) * 1.5, 1)
            history.append({
                "measured_at": t.isoformat(),
                "pm25": pm,
                "aqi": pm25_aqi(pm),
                "co2": 620,
                "noise_db": 56.0,
                "temperature": 31.0,
                "source": "simulator",
            })
        return history

    def list_stations(self) -> list[dict[str, Any]]:
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
                        return self._fallback_stations()
                    stations = [self._shape_station(row) for row in rows]
                    if all(st.get("pm25") is None for st in stations):
                        return self._fallback_stations()
                    return stations
        except Exception:
            return self._fallback_stations()

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
                    return station
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
        now = datetime.now(timezone.utc)
        return (now - last_seen.astimezone(timezone.utc)).total_seconds() > self.stale_after_seconds
