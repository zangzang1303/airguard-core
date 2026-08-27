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


def test_spatial_fourier_forecast_24h_horizons(sample_history):
    service = ProphetForecastService()
    res = service.forecast(station_id="S01", history=sample_history, hours=24, metric="pm25")

    assert res["station_id"] == "S01"
    assert res["metric"] == "pm25"
    assert res["model"] == "spatial_fourier_heuristic_v2"
    assert res["source"] == "simulator_history_spatial_fourier_v2"
    assert len(res["horizons"]) == 24

    for h in res["horizons"]:
        assert h["hours_ahead"] >= 1
        assert h["lower_bound"] <= h["predicted_value"] <= h["upper_bound"]
        assert 0.0 <= h["confidence"] <= 1.0

    assert "trend_summary" in res
    assert len(res["trend_summary"]) > 20
    assert "thích hợp cho hoạt động ngoài trời" not in res["trend_summary"]
    assert "dữ liệu simulator" in res["trend_summary"]


def test_spatial_fourier_forecast_multi_metrics(sample_history):
    service = ProphetForecastService()
    for metric in ["pm25", "aqi", "co2", "noise_db", "temperature"]:
        res = service.forecast(station_id="S03", history=sample_history, hours=12, metric=metric)
        assert res["metric"] == metric
        assert len(res["horizons"]) == 12
        for item in res["horizons"]:
            assert item["predicted_value"] is not None


def test_spatial_fourier_forecast_sub_50ms_latency(sample_history):
    service = ProphetForecastService()
    start = time.perf_counter()
    service.forecast(station_id="S02", history=sample_history, hours=24, metric="pm25")
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert elapsed_ms < 50.0, f"Spatial Fourier forecast took {elapsed_ms:.2f}ms (must be < 50ms)"


def test_spatial_heuristic_fails_closed_without_history():
    service = ProphetForecastService()

    with pytest.raises(ValueError, match="at least three"):
        service.forecast(station_id="S01", history=[], hours=3, metric="pm25")


def test_spatial_heuristic_anchors_an_abrupt_spike():
    service = ProphetForecastService()
    now = datetime.now(UTC)
    history = [
        {"measured_at": (now - timedelta(minutes=20)).isoformat(), "pm25": 40.0},
        {"measured_at": (now - timedelta(minutes=10)).isoformat(), "pm25": 40.0},
        {"measured_at": now.isoformat(), "pm25": 190.0},
    ]

    result = service.forecast(station_id="S01", history=history, hours=1, metric="pm25")

    assert result["horizons"][0]["predicted_value"] >= 140.0


def test_spatial_heuristic_accepts_database_datetime_timestamps():
    service = ProphetForecastService()
    now = datetime.now(UTC)
    history = [
        {"measured_at": now - timedelta(minutes=20), "pm25": 40.0},
        {"measured_at": now - timedelta(minutes=10), "pm25": 42.0},
        {"measured_at": now, "pm25": 44.0},
    ]

    result = service.forecast(station_id="S01", history=history, hours=1, metric="pm25")

    assert len(result["horizons"]) == 1
