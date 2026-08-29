from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))


def load_app_without_database():
    os.environ.pop("DATABASE_URL", None)
    import app.main as main_module

    return main_module


def extended_history() -> list[dict]:
    start = datetime(2026, 8, 26, 0, 0, tzinfo=UTC)
    return [
        {
            "measured_at": start + timedelta(hours=index),
            "pm25": 18.0 + (index % 24) * 0.15,
            "co2": 520.0 + (index % 24) * 2.0,
            "noise_db": 48.0 + (index % 8),
            "temperature": 31.0 - (index % 8) * 0.2,
            "humidity": 84.0 if index % 24 >= 22 or index % 24 <= 5 else 70.0,
            "wind_speed": 2.8,
            "source": "simulator",
        }
        for index in range(72)
    ]


def test_baseline_rejects_horizon_above_three_without_reading_history() -> None:
    main_module = load_app_without_database()
    client = TestClient(main_module.app)

    with patch.object(main_module.station_service, "get_forecast_history") as history:
        response = client.get(
            "/api/v1/stations/S01/forecast",
            params={"hours": 24, "metric": "pm25", "model": "baseline"},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "forecast_horizon_unsupported"
    history.assert_not_called()


def test_extended_forecast_returns_24_grounded_hourly_points() -> None:
    main_module = load_app_without_database()
    client = TestClient(main_module.app)

    with patch.object(
        main_module.station_service,
        "get_extended_forecast_history",
        return_value=extended_history(),
    ):
        response = client.get(
            "/api/v1/stations/S01/forecast",
            params={"hours": 24, "metric": "aqi", "model": "extended"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["model_name"] == "extended_additive_fourier_v3"
    assert body["source"] == "simulator_history_additive_fourier_v3"
    assert body["freshness"] == "fresh"
    assert len(body["items"]) == 24
    assert all(item["forecast_at"].endswith("+00:00") for item in body["items"])
    assert all(item["value_min"] <= item["value"] <= item["value_max"] for item in body["items"])


def test_golden_window_endpoint_returns_criteria_and_worst_point() -> None:
    main_module = load_app_without_database()
    client = TestClient(main_module.app)

    with patch.object(
        main_module.station_service,
        "get_extended_forecast_history",
        return_value=extended_history(),
    ):
        response = client.get(
            "/api/v1/forecast/golden-windows",
            params={"station_id": "S03", "minimum_wind_speed": 2.0},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["station_id"] == "S03"
    assert body["criteria"] == {
        "maximum_aqi": 50,
        "minimum_wind_speed": 2.0,
        "minimum_duration_hours": 2,
    }
    assert body["worst_window"]["aqi"] >= 0
    assert body["source"] == "simulator_history_additive_fourier_v3"
