from __future__ import annotations

from datetime import UTC, datetime


class WeatherService:
    def current_weather(self) -> dict[str, object]:
        return {
            "area_id": "vinuni-ocean-park",
            "temperature": 31.5,
            "humidity": 72,
            "wind_speed": 2.4,
            "rainfall": 0,
            "source": "simulator_fallback_weather",
            "observed_at": datetime.now(UTC).isoformat(),
            "is_fallback": True,
            "is_stale": False,
        }
