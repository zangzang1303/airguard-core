from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any

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
        self._demo_overrides: dict[str, dict[str, float]] = {}
        self._demo_override_started_at: dict[str, datetime] = {}
        self._ventilation_cycles: dict[str, dict[str, Any]] = {}
        self._bootstrap_history()

    def _bootstrap_history(self) -> None:
        """Seed rolling 72-hour realistic history for each station."""
        now = datetime.now(UTC)
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
        now = datetime.now(UTC)
        for s in self.STATION_DEFINITIONS:
            st_id = s["station_id"]
            m = self._calculate_measurement_at(s, now)
            override = self._demo_overrides.get(st_id)
            if override:
                m.update(override)
                m["aqi"] = pm25_aqi(float(m["pm25"]))
                m["aqi_category"] = aqi_category(m["aqi"])
                m["level"] = pm25_level(float(m["pm25"]))
                m["demo_override"] = True
                m["demo_override_note"] = "Demo operator override; automatic simulator remains running."
            m = self._apply_ventilation_feedback(m, now)
            self._history[st_id].append(m)
            if len(self._history[st_id]) > 200:
                self._history[st_id] = self._history[st_id][-200:]

    def get_current_stations(self) -> list[dict[str, Any]]:
        self.tick()
        now = datetime.now(UTC)
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
        all_pts = self._history.get(station_id, [])
        now = datetime.now(UTC)
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

    def get_latest(self, station_id: str) -> dict[str, Any]:
        if self._history.get(station_id):
            return self._history[station_id][-1]
        return self._calculate_measurement_at(self.STATION_DEFINITIONS[0], datetime.now(UTC))

    def get_all_histories(self, hours: int = 48) -> dict[str, list[dict[str, Any]]]:
        return {s["station_id"]: self.get_history(s["station_id"], hours=hours) for s in self.STATION_DEFINITIONS}

    def update_station(self, station_id: str, overrides: dict[str, Any]) -> None:
        """Testing & simulation override helper."""
        now = datetime.now(UTC)
        curr = self.get_latest(station_id)
        updated = {**curr, **overrides, "station_id": station_id, "measured_at": now.isoformat(), "timestamp": now.isoformat()}
        self._history[station_id].append(updated)
        if len(self._history[station_id]) >= 5:
            for i in range(-5, 0):
                self._history[station_id][i].update(overrides)

    def set_demo_override(self, station_id: str, values: dict[str, float]) -> dict[str, Any]:
        if station_id not in self._history:
            raise KeyError(station_id)
        self._demo_overrides[station_id] = dict(values)
        self._demo_override_started_at[station_id] = datetime.now(UTC)
        self.tick()
        return self.get_latest(station_id)

    def clear_demo_override(self, station_id: str) -> None:
        self._demo_overrides.pop(station_id, None)
        self._demo_override_started_at.pop(station_id, None)
        self.tick()

    def get_demo_overrides(self) -> dict[str, dict[str, float]]:
        return {station_id: dict(values) for station_id, values in self._demo_overrides.items()}

    def get_demo_override_evidence(self, station_id: str) -> dict[str, Any] | None:
        values = self._demo_overrides.get(station_id)
        started_at = self._demo_override_started_at.get(station_id)
        if values is None or started_at is None:
            return None
        return {
            **values,
            "started_at": started_at,
            "source": "demo_override",
        }

    def apply_demo_override(self, station: dict[str, Any]) -> dict[str, Any]:
        override = self._demo_overrides.get(str(station.get("station_id")))
        if not override:
            return self._apply_ventilation_feedback(dict(station), datetime.now(UTC))
        updated = {**station, **override, "demo_override": True, "demo_override_note": "Demo operator override; automatic simulator remains running."}
        updated["aqi"] = pm25_aqi(float(updated["pm25"]))
        updated["aqi_category"] = aqi_category(updated["aqi"])
        updated["level"] = pm25_level(float(updated["pm25"]))
        return self._apply_ventilation_feedback(updated, datetime.now(UTC))

    def sync_ventilation_devices(self, devices: list[dict[str, Any]]) -> None:
        active_stations: set[str] = set()
        for device in devices:
            station_id = str(device.get("station_id") or "")
            command = device.get("latest_command") or {}
            command_id = command.get("command_id") or command.get("command_intent_id")
            if not station_id or not command_id or not device.get("is_active"):
                continue
            active_stations.add(station_id)
            existing = self._ventilation_cycles.get(station_id)
            if existing and existing.get("command_id") == command_id:
                continue
            self._ventilation_cycles[station_id] = {
                "command_id": command_id,
                "started_at": device.get("started_at"),
                "ends_at": device.get("ends_at"),
                "intensity_percent": device.get("intensity_percent") or 80,
                "baseline_pm25": None,
                "baseline_co2": None,
            }
        for station_id in tuple(self._ventilation_cycles):
            if station_id not in active_stations:
                self._ventilation_cycles.pop(station_id, None)

    def _apply_ventilation_feedback(self, measurement: dict[str, Any], now: datetime) -> dict[str, Any]:
        station_id = str(measurement.get("station_id") or "")
        cycle = self._ventilation_cycles.get(station_id)
        if not cycle or measurement.get("pm25") is None or measurement.get("co2") is None:
            return measurement
        started_at_raw = cycle.get("started_at")
        ends_at_raw = cycle.get("ends_at")
        if not started_at_raw or not ends_at_raw:
            return measurement
        started_at = datetime.fromisoformat(str(started_at_raw)).astimezone(UTC)
        ends_at = datetime.fromisoformat(str(ends_at_raw)).astimezone(UTC)
        if now >= ends_at:
            self._ventilation_cycles.pop(station_id, None)
            return measurement
        if cycle.get("baseline_pm25") is None:
            cycle["baseline_pm25"] = float(measurement["pm25"])
            cycle["baseline_co2"] = float(measurement["co2"])
        elapsed_minutes = max(0.0, (now - started_at).total_seconds() / 60.0)
        intensity_scale = max(0.1, float(cycle.get("intensity_percent") or 80) / 80.0)
        pm25_target = 15.0
        co2_target = 450.0
        pm25 = (
            (max(pm25_target, float(cycle["baseline_pm25"])) - pm25_target)
            * math.exp(-0.08 * intensity_scale * elapsed_minutes)
            + pm25_target
        )
        co2 = (
            (max(co2_target, float(cycle["baseline_co2"])) - co2_target)
            * math.exp(-0.06 * intensity_scale * elapsed_minutes)
            + co2_target
        )
        updated = dict(measurement)
        updated["pm25"] = round(min(float(measurement["pm25"]), pm25), 1)
        updated["co2"] = round(min(float(measurement["co2"]), co2), 1)
        updated["aqi"] = pm25_aqi(updated["pm25"])
        updated["aqi_category"] = aqi_category(updated["aqi"])
        updated["level"] = pm25_level(updated["pm25"])
        updated["ventilation_feedback"] = {
            "command_id": cycle["command_id"],
            "model": "task4_exponential_decay_v1",
            "is_simulated": True,
        }
        return updated


# Global singleton
live_engine = LiveTelemetryEngine()
