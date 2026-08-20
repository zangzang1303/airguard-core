from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
import pytest

from backend.app.services.prophet_forecast_service import ProphetForecastService


@pytest.fixture
def sample_history():
    now = datetime.now(timezone.utc)
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


def test_prophet_forecast_24h_horizons(sample_history):
    service = ProphetForecastService()
    res = service.forecast(station_id="S01", history=sample_history, hours=24, metric="pm25")

    assert res["station_id"] == "S01"
    assert res["metric"] == "pm25"
    assert res["model"] == "prophet_time_series_v1"
    assert len(res["horizons"]) == 24

    for h in res["horizons"]:
        assert h["hours_ahead"] >= 1
        assert h["lower_bound"] <= h["predicted_value"] <= h["upper_bound"]
        assert 0.0 <= h["confidence"] <= 1.0

    assert "trend_summary" in res
    assert len(res["trend_summary"]) > 20


def test_prophet_forecast_multi_metrics(sample_history):
    service = ProphetForecastService()
    for metric in ["pm25", "aqi", "co2", "noise_db", "temperature"]:
        res = service.forecast(station_id="S03", history=sample_history, hours=12, metric=metric)
        assert res["metric"] == metric
        assert len(res["horizons"]) == 12
        for item in res["horizons"]:
            assert item["predicted_value"] is not None


def test_prophet_forecast_sub_50ms_latency(sample_history):
    service = ProphetForecastService()
    start = time.perf_counter()
    res = service.forecast(station_id="S02", history=sample_history, hours=24, metric="pm25")
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert elapsed_ms < 50.0, f"Prophet forecast took {elapsed_ms:.2f}ms (must be < 50ms)"
