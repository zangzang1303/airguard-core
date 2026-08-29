from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import pytest

from backend.app.services.prophet_forecast_service import ProphetForecastService


@pytest.fixture
def sample_history():
    now = datetime.now(UTC)
    return [
        {
            "measured_at": (now - timedelta(hours=i)).isoformat(),
            "pm25": 42.0 + (i % 6 - 3) * 2.0,
            "aqi": 115 + (i % 6 - 3) * 5,
            "co2": 650.0 + (i % 8 - 4) * 20.0,
            "noise_db": 56.0 + (i % 4 - 2) * 3.0,
            "temperature": 31.0 + (i % 12 - 6) * 0.5,
        }
        for i in range(48)
    ]


def test_extended_additive_forecast_24h_horizons(sample_history):
    service = ProphetForecastService()
    res = service.forecast(station_id="S01", history=sample_history, hours=24, metric="pm25")

    assert res["station_id"] == "S01"
    assert res["metric"] == "pm25"
    assert res["model"] == "extended_additive_fourier_v3"
    assert res["source"] == "simulator_history_additive_fourier_v3"
    assert len(res["horizons"]) == 24

    for h in res["horizons"]:
        assert h["hours_ahead"] >= 1
        assert h["lower_bound"] <= h["predicted_value"] <= h["upper_bound"]
        assert 0.0 <= h["confidence"] <= 1.0

    assert "trend_summary" in res
    assert len(res["trend_summary"]) > 20
    assert "thích hợp cho hoạt động ngoài trời" not in res["trend_summary"]
    assert "dữ liệu simulator" in res["trend_summary"]
    assert "không phải thư viện Prophet" in res["limitations"][0]


def test_extended_additive_forecast_multi_metrics(sample_history):
    service = ProphetForecastService()
    for metric in ["pm25", "aqi", "co2", "noise_db", "temperature"]:
        res = service.forecast(station_id="S03", history=sample_history, hours=12, metric=metric)
        assert res["metric"] == metric
        assert len(res["horizons"]) == 12
        for item in res["horizons"]:
            assert item["predicted_value"] is not None


def test_extended_additive_forecast_sub_50ms_latency(sample_history):
    service = ProphetForecastService()
    start = time.perf_counter()
    service.forecast(station_id="S02", history=sample_history, hours=24, metric="pm25")
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert elapsed_ms < 50.0, f"Spatial Fourier forecast took {elapsed_ms:.2f}ms (must be < 50ms)"


def test_extended_forecast_fails_closed_without_history():
    service = ProphetForecastService()

    with pytest.raises(ValueError, match="at least three"):
        service.forecast(station_id="S01", history=[], hours=3, metric="pm25")


def test_extended_forecast_anchors_an_abrupt_spike():
    service = ProphetForecastService()
    now = datetime.now(UTC)
    history = [
        {
            "measured_at": (now - timedelta(hours=11 - index)).isoformat(),
            "pm25": 190.0 if index == 11 else 40.0,
        }
        for index in range(12)
    ]

    result = service.forecast(station_id="S01", history=history, hours=1, metric="pm25")

    assert result["horizons"][0]["predicted_value"] >= 140.0


def test_extended_forecast_accepts_database_datetime_timestamps():
    service = ProphetForecastService()
    now = datetime.now(UTC)
    history = [
        {
            "measured_at": now - timedelta(hours=11 - index),
            "pm25": 40.0 + index,
        }
        for index in range(12)
    ]

    result = service.forecast(station_id="S01", history=history, hours=1, metric="pm25")

    assert len(result["horizons"]) == 1


def test_traffic_modifier_only_applies_to_documented_stations():
    service = ProphetForecastService()
    morning_rush_utc = datetime(2026, 8, 29, 0, 0, tzinfo=UTC)  # 07:00 ICT

    assert service._traffic_modifier("S01", morning_rush_utc, "pm25") == 8.5
    assert service._traffic_modifier("S05", morning_rush_utc, "pm25") == 8.5
    assert service._traffic_modifier("S03", morning_rush_utc, "pm25") == 0.0
    assert service._traffic_modifier("S01", morning_rush_utc, "co2") == 0.0


def test_nocturnal_inversion_requires_humidity_and_temperature_drop():
    service = ProphetForecastService()
    nighttime_utc = datetime(2026, 8, 28, 16, 0, tzinfo=UTC)  # 23:00 ICT

    assert service._inversion_modifier(
        nighttime_utc,
        {"humidity": 84.0, "temperature_drop_c": -0.8},
        "pm25",
    ) == 3.5
    assert service._inversion_modifier(
        nighttime_utc,
        {"humidity": 79.0, "temperature_drop_c": -0.8},
        "pm25",
    ) == 0.0


def test_golden_windows_require_two_contiguous_safe_windy_hours():
    service = ProphetForecastService()
    start = datetime(2026, 8, 29, 0, 0, tzinfo=UTC)
    values = [65, 42, 35, 70]
    forecast = {
        "station_id": "S03",
        "metric": "aqi",
        "generated_at": start.isoformat(),
        "source": service.SOURCE,
        "model_name": service.MODEL_NAME,
        "limitations": ["simulator"],
        "items": [
            {
                "forecast_at": (start + timedelta(hours=index + 1)).isoformat(),
                "value": value,
                "weather_context": {"wind_speed": 2.5},
            }
            for index, value in enumerate(values)
        ],
    }

    result = service.golden_windows(forecast)

    assert result["best_window"]["duration_hours"] == 2
    assert result["best_window"]["minimum_aqi"] == 35
    assert result["worst_window"]["aqi"] == 70
