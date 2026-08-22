from __future__ import annotations

from math import floor

# US EPA PM2.5 24-hour concentration breakpoints. The result is a simulator
# sub-index, not an official AQI/NowCast observation.
_BREAKPOINTS = (
    (0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
)


def pm25_aqi(pm25: float | None) -> int | None:
    if pm25 is None:
        return None
    concentration = floor(float(pm25) * 10) / 10
    for low, high, index_low, index_high in _BREAKPOINTS:
        if low <= concentration <= high:
            return round((index_high - index_low) * (concentration - low) / (high - low) + index_low)
    return 500 if concentration > 500.4 else 0


def aqi_category(aqi: int | None) -> str | None:
    if aqi is None:
        return None
    if aqi <= 50:
        return "good"
    if aqi <= 100:
        return "moderate"
    if aqi <= 150:
        return "unhealthy_sensitive"
    if aqi <= 200:
        return "unhealthy"
    if aqi <= 300:
        return "very_unhealthy"
    return "hazardous"
