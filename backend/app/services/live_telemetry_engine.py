from __future__ import annotations

import math
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from .air_quality import pm25_aqi, aqi_category


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


class LiveTelemetryEngine:
    """
    In-memory live continuous telemetry and time-series generator for AirGuard AI.
    Ensures that when running on Render/Cloud or standalone, the telemetry dynamically
    evolves in real-time with diurnal traffic curves, wind drifts, and natural sensor oscillations.
    """

    STATION_DEFINITIONS = [
        {
            "station_id": "S01",
            "station_name": "Trục Đa Tốn phía Tây Bắc",
            "location_type": "northwest_road",
            "latitude": 21.0008,
            "longitude": 105.9428,
            "base_pm25": 42.0,
            "base_co2": 650.0,
            "base_noise": 62.0,
            "base_temp": 31.0,
            "description": "Điểm mô phỏng trên trục Đa Tốn, phủ khu vực cửa ngõ Tây Bắc Ocean Park 1",
        },
        {
            "station_id": "S02",
            "station_name": "Khu căn hộ Sapphire",
            "location_type": "high_rise_residential",
            "latitude": 20.9975,
            "longitude": 105.9430,
            "base_pm25": 38.0,
            "base_co2": 710.0,
            "base_noise": 58.0,
            "base_temp": 31.5,
            "description": "Điểm mô phỏng trong cụm căn hộ phía Tây Bắc, đại diện khu dân cư mật độ cao",
        },
        {
            "station_id": "S03",
            "station_name": "Ven Hồ Ngọc Trai",
            "location_type": "lakeside_residential",
            "latitude": 20.9953,
            "longitude": 105.9500,
            "base_pm25": 32.0,
            "base_co2": 580.0,
            "base_noise": 51.0,
            "base_temp": 30.5,
            "description": "Điểm mô phỏng ven Hồ Ngọc Trai và khu Ngọc Trai, đại diện không gian ven hồ trung tâm",
        },
        {
            "station_id": "S04",
            "station_name": "Khuôn viên VinUni",
            "location_type": "university_campus",
            "latitude": 20.9898,
            "longitude": 105.9467,
            "base_pm25": 28.0,
            "base_co2": 530.0,
            "base_noise": 48.0,
            "base_temp": 30.0,
            "description": "Điểm mô phỏng trong khuôn viên VinUni ở phía Tây Nam phạm vi quan sát",
        },
        {
            "station_id": "S05",
            "station_name": "Khu Hải Âu phía Đông Nam",
            "location_type": "southeast_residential",
            "latitude": 20.9910,
            "longitude": 105.9560,
            "base_pm25": 45.0,
            "base_co2": 670.0,
            "base_noise": 60.0,
            "base_temp": 31.2,
            "description": "Điểm mô phỏng tại khu Hải Âu, phủ vùng dân cư phía Đông Nam Ocean Park 1",
        },
    ]

    def __init__(self) -> None:
        self._history: dict[str, list[dict[str, Any]]] = {s["station_id"]: [] for s in self.STATION_DEFINITIONS}
        self._bootstrap_history()

    def _bootstrap_history(self) -> None:
        """Seed rolling 72-hour realistic history for each station."""
        now = datetime.now(timezone.utc)
        for s in self.STATION_DEFINITIONS:
            st_id = s["station_id"]
            history_list = []
            for i in range(144, -1, -1):  # 144 steps of 30 minutes = 72 hours
                t = now - timedelta(minutes=i * 30)
                m = self._calculate_measurement_at(s, t)
                history_list.append(m)
            self._history[st_id] = history_list

    def _calculate_measurement_at(self, station: dict[str, Any], t: datetime) -> dict[str, Any]:
        hour = t.hour
        local_hour = (hour + 7) % 24
        is_rush = (7 <= local_hour <= 9) or (17 <= local_hour <= 19)
        rush_boost = 14.0 if is_rush else 0.0

        time_factor = math.sin((local_hour - 6) / 24.0 * 2 * math.pi) * 6.0
        sec_hash = int(t.timestamp()) % 3600
        jitter = math.sin(sec_hash * 0.05 + int(station["station_id"][-1]) * 1.7) * 4.2

        pm25 = max(10.0, round(station["base_pm25"] + rush_boost + time_factor + jitter, 1))
        co2 = max(400.0, round(station["base_co2"] + (rush_boost * 8.0) + (time_factor * 15.0) + (jitter * 12.0), 1))
        noise = max(35.0, round(station["base_noise"] + (rush_boost * 0.4) + (time_factor * 1.5) + (jitter * 0.9), 1))
        temp = round(station["base_temp"] + (time_factor * 0.5) + (jitter * 0.2), 1)
        humidity = max(40.0, min(95.0, round(70.0 - (time_factor * 2.0) + (jitter * 1.5), 1)))

        aqi = pm25_aqi(pm25)
        iso_str = t.isoformat()

        return {
            "station_id": station["station_id"],
            "station_name": station["station_name"],
            "location_type": station["location_type"],
            "latitude": station["latitude"],
            "longitude": station["longitude"],
            "description": station["description"],
            "message_id": f"MSG-{station['station_id']}-{int(t.timestamp())}",
            "measured_at": iso_str,
            "received_at": iso_str,
            "timestamp": iso_str,
            "updated_at": iso_str,
            "last_seen_at": iso_str,
            "active": True,
            "pm25": pm25,
            "aqi": aqi,
            "aqi_category": aqi_category(aqi),
            "aqi_standard": "US_EPA_PM25_24H_2012",
            "co2": co2,
            "noise_db": noise,
            "temperature": temp,
            "humidity": humidity,
            "level": pm25_level(pm25),
            "status": "online",
            "is_stale": False,
            "freshness": "fresh",
            "source": "simulator",
            "quality_flag": "valid",
        }

    def tick(self) -> None:
        """Advance live sensor measurements."""
        now = datetime.now(timezone.utc)
        for s in self.STATION_DEFINITIONS:
            st_id = s["station_id"]
            m = self._calculate_measurement_at(s, now)
            self._history[st_id].append(m)
            if len(self._history[st_id]) > 200:
                self._history[st_id] = self._history[st_id][-200:]

    def get_current_stations(self) -> list[dict[str, Any]]:
        self.tick()
        now = datetime.now(timezone.utc)
        result = []
        for s in self.STATION_DEFINITIONS:
            st_id = s["station_id"]
            if self._history[st_id]:
                curr = self._history[st_id][-1]
            else:
                curr = self._calculate_measurement_at(s, now)
            result.append(curr)
        return result

    def get_current_station(self, station_id: str) -> dict[str, Any] | None:
        stations = self.get_current_stations()
        return next((s for s in stations if s["station_id"] == station_id), None)

    def get_history(self, station_id: str, hours: int = 24) -> list[dict[str, Any]]:
        self.tick()
        all_pts = self._history.get(station_id, [])
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=hours)
        filtered = [p for p in all_pts if datetime.fromisoformat(p["measured_at"].replace("Z", "+00:00")) >= cutoff]
        return filtered if filtered else all_pts[-min(len(all_pts), hours * 2):]

    def get_forecast_history(self, station_id: str) -> list[dict[str, Any]]:
        history = self.get_history(station_id, hours=3)
        return [
            {
                "measured_at": p["measured_at"],
                "pm25": p["pm25"],
                "aqi": p["aqi"],
                "co2": p["co2"],
                "noise_db": p["noise_db"],
                "temperature": p["temperature"],
                "source": "simulator",
            }
            for p in history[-12:]
        ]


# Global singleton
live_engine = LiveTelemetryEngine()
