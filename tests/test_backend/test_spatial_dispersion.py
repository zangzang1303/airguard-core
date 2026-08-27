from __future__ import annotations

import math
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Any, TypeVar

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.services.database import Database, ServiceError
from backend.app.services.spatial_dispersion_service import SpatialDispersionService
from backend.app.services.station_service import StationService
from src.agents.tools.contracts import SpatialAirQuality

STATION_COORDINATES = {
    "S01": (21.0008, 105.9428),
    "S02": (20.9975, 105.9430),
    "S03": (20.9953, 105.9500),
    "S04": (20.9898, 105.9467),
    "S05": (20.9910, 105.9560),
}

T = TypeVar("T")


def measure_best_ms(operation: Callable[[], T], *, attempts: int = 3) -> tuple[T, float]:
    """Measure steady-state latency without failing on a single scheduler pause."""
    operation()
    samples: list[tuple[T, float]] = []
    for _ in range(attempts):
        started_at = perf_counter()
        result = operation()
        samples.append((result, (perf_counter() - started_at) * 1000))
    return min(samples, key=lambda sample: sample[1])


class FakeStationService:
    def __init__(
        self,
        stations: list[dict[str, Any]],
        histories: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.stations = stations
        self.histories = histories or {}

    def list_stations(self, *, allow_fallback: bool = True) -> list[dict[str, Any]]:
        assert allow_fallback is False
        return [dict(station) for station in self.stations]

    def get_forecast_history(self, station_id: str) -> list[dict[str, Any]]:
        return [dict(item) for item in self.histories.get(station_id, [])]


class StaticRowsCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def __enter__(self) -> StaticRowsCursor:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, _query: str) -> None:
        return None

    def fetchall(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows]


class StaticRowsConnection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def cursor(self, **_kwargs: object) -> StaticRowsCursor:
        return StaticRowsCursor(self.rows)


class StaticRowsDatabase:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    @contextmanager
    def connection(self):
        yield StaticRowsConnection(self.rows)


class FakeWeatherProvider:
    def __init__(
        self,
        *,
        speed: float = 3.2,
        direction: float | None = 135,
        is_stale: bool = False,
    ) -> None:
        self.speed = speed
        self.direction = direction
        self.is_stale = is_stale

    def current_weather(self) -> dict[str, object]:
        weather: dict[str, object] = {
            "wind_speed": self.speed,
            "source": "simulator_fallback_weather",
            "observed_at": "2026-08-21T02:00:00+00:00",
            "is_fallback": True,
            "is_stale": self.is_stale,
        }
        if self.direction is not None:
            weather["wind_direction"] = self.direction
        return weather


class FakeForecastProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def forecast(
        self,
        station_id: str,
        history: list[dict[str, Any]],
        hours: int,
        metric: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "station_id": station_id,
                "history_points": len(history),
                "hours": hours,
                "metric": metric,
            }
        )
        current = float(history[-1][metric])
        return {
            "source": "test_forecast_v1",
            "horizons": [
                {
                    "hours_ahead": hour,
                    "predicted_value": current + hour,
                    "timestamp": (datetime(2026, 8, 21, tzinfo=UTC) + timedelta(hours=hour)).isoformat(),
                }
                for hour in range(1, hours + 1)
            ],
        }


def make_stations() -> list[dict[str, Any]]:
    observed_at = "2026-08-21T02:00:00+00:00"
    stations: list[dict[str, Any]] = []
    for index, (station_id, (latitude, longitude)) in enumerate(STATION_COORDINATES.items()):
        pm25 = 25.0 + index * 8.0
        stations.append(
            {
                "station_id": station_id,
                "latitude": latitude,
                "longitude": longitude,
                "active": True,
                "status": "online",
                "is_stale": False,
                "freshness": "fresh",
                "quality_flag": "valid",
                "pm25": pm25,
                "aqi": 50.0 + index * 20.0,
                "co2": 600.0 + index * 100.0,
                "noise_db": 50.0 + index * 5.0,
                "temperature": 28.0 + index,
                "updated_at": observed_at,
                "source": "simulator",
            }
        )
    return stations


def make_histories(stations: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    start = datetime(2026, 8, 21, tzinfo=UTC)
    histories: dict[str, list[dict[str, Any]]] = {}
    for station in stations:
        histories[station["station_id"]] = [
            {
                "measured_at": (start + timedelta(minutes=30 * index)).isoformat(),
                "pm25": float(station["pm25"]) + index,
                "aqi": float(station["aqi"]) + index,
                "co2": float(station["co2"]) + index,
                "noise_db": float(station["noise_db"]) + index,
                "temperature": float(station["temperature"]) + index * 0.1,
                "quality_flag": "valid",
                "source": "simulator",
            }
            for index in range(4)
        ]
    return histories


def make_database_station_rows(*, observed_at: datetime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for station in make_stations():
        rows.append(
            {
                "station_id": station["station_id"],
                "station_name": f"Station {station['station_id']}",
                "location_type": "test",
                "latitude": station["latitude"],
                "longitude": station["longitude"],
                "description": "Spatial strict-mode test station",
                "active": True,
                "pm25": station["pm25"],
                "co2": station["co2"],
                "noise_db": station["noise_db"],
                "temperature": station["temperature"],
                "updated_at": observed_at,
                "source": "simulator",
                "explicit_status": "online",
                "last_seen_at": observed_at,
            }
        )
    return rows


def make_service(
    stations: list[dict[str, Any]] | None = None,
    *,
    weather: FakeWeatherProvider | None = None,
    forecast: FakeForecastProvider | None = None,
) -> SpatialDispersionService:
    station_rows = stations or make_stations()
    return SpatialDispersionService(
        FakeStationService(station_rows, make_histories(station_rows)),  # type: ignore[arg-type]
        weather_provider=weather or FakeWeatherProvider(),
        forecast_provider=forecast or FakeForecastProvider(),
    )


def test_current_heatmap_is_clipped_smooth_finite_and_under_200_ms() -> None:
    service = make_service()

    result, elapsed_ms = measure_best_ms(
        lambda: service.calculate_heatmap(metric="aqi", forecast_hour=0)
    )

    assert elapsed_ms < 200, f"spatial calculation took {elapsed_ms:.2f} ms"
    assert 0 < len(result["grid_points"]) < service.GRID_ROWS * service.GRID_COLS
    assert result["data_quality"]["stations_used"] == ["S01", "S02", "S03", "S04", "S05"]
    assert result["data_quality"]["stations_excluded"] == []
    assert all(
        service._is_inside_boundary(point["lat"], point["lon"])
        for point in result["grid_points"]
    )
    assert all(math.isfinite(point["value"]) for point in result["grid_points"])
    assert all(50.0 <= point["value"] <= 130.0 for point in result["grid_points"])

    rows: dict[float, list[dict[str, Any]]] = {}
    for point in result["grid_points"]:
        rows.setdefault(point["lat"], []).append(point)
    neighbour_deltas = [
        abs(current["value"] - previous["value"])
        for row in rows.values()
        for previous, current in zip(sorted(row, key=lambda item: item["lon"]), sorted(row, key=lambda item: item["lon"])[1:])
    ]
    assert neighbour_deltas
    assert max(neighbour_deltas) < 25.0


def test_idw_returns_exact_station_value_without_division_by_zero() -> None:
    station_inputs = [
        {"lat": 20.99, "lon": 105.95, "value": 123.4},
        {"lat": 20.98, "lon": 105.94, "value": 30.0},
        {"lat": 21.00, "lon": 105.96, "value": 40.0},
    ]

    result = SpatialDispersionService._interpolate_value_at(
        20.99,
        105.95,
        station_inputs,
        wind_speed_ms=12.0,
        wind_direction_deg=90,
    )

    assert result == 123.4


def test_wind_speed_stretches_effective_distance_downwind() -> None:
    calm = SpatialDispersionService._effective_distance(
        1.0,
        direction_cosine=1.0,
        wind_speed_ms=0.0,
    )
    downwind_slow = SpatialDispersionService._effective_distance(
        1.0,
        direction_cosine=1.0,
        wind_speed_ms=2.0,
    )
    downwind_fast = SpatialDispersionService._effective_distance(
        1.0,
        direction_cosine=1.0,
        wind_speed_ms=6.0,
    )
    upwind_fast = SpatialDispersionService._effective_distance(
        1.0,
        direction_cosine=-1.0,
        wind_speed_ms=6.0,
    )

    assert downwind_fast < downwind_slow < calm < upwind_fast


def test_wind_adjustment_elongates_high_value_plume_downwind() -> None:
    station_inputs = [
        {"lat": 20.995, "lon": 105.948, "value": 120.0},
        {"lat": 20.990, "lon": 105.948, "value": 20.0},
        {"lat": 21.000, "lon": 105.948, "value": 20.0},
    ]
    east = 105.953
    west = 105.943

    calm_east = SpatialDispersionService._interpolate_value_at(
        20.995,
        east,
        station_inputs,
        wind_speed_ms=0.0,
        wind_direction_deg=90,
    )
    windy_east = SpatialDispersionService._interpolate_value_at(
        20.995,
        east,
        station_inputs,
        wind_speed_ms=6.0,
        wind_direction_deg=90,
    )
    windy_west = SpatialDispersionService._interpolate_value_at(
        20.995,
        west,
        station_inputs,
        wind_speed_ms=6.0,
        wind_direction_deg=90,
    )

    assert windy_east > calm_east
    assert windy_east > windy_west


def test_offline_stale_and_invalid_stations_are_excluded() -> None:
    stations = make_stations()
    stations[3]["status"] = "offline"
    stations[4]["quality_flag"] = "invalid"
    stations[4]["updated_at"] = None

    result = make_service(stations).calculate_heatmap("pm25", 0)

    assert result["data_quality"]["stations_used"] == ["S01", "S02", "S03"]
    assert result["data_quality"]["stations_excluded"] == ["S04", "S05"]
    assert "not_online" in result["data_quality"]["exclusion_reasons"]["S04"]
    assert "invalid_quality" in result["data_quality"]["exclusion_reasons"]["S05"]
    assert "missing_or_invalid_timestamp" in result["data_quality"]["exclusion_reasons"]["S05"]


def test_fewer_than_three_usable_stations_returns_structured_error() -> None:
    stations = make_stations()
    for station in stations[2:]:
        station["is_stale"] = True
        station["freshness"] = "stale"

    with pytest.raises(ServiceError) as exc_info:
        make_service(stations).calculate_heatmap("aqi", 0)

    error = exc_info.value
    assert error.code == "insufficient_spatial_data"
    assert error.status_code == 503
    assert error.details is not None
    assert error.details["stations_usable"] == 2
    assert error.details["stations_required"] == 3


def test_real_station_service_strict_mode_does_not_replace_stale_rows() -> None:
    stale_at = datetime.now(UTC) - timedelta(minutes=30)
    station_service = StationService(
        StaticRowsDatabase(make_database_station_rows(observed_at=stale_at)),  # type: ignore[arg-type]
        stale_after_seconds=300,
    )

    service = SpatialDispersionService(
        station_service,
        weather_provider=FakeWeatherProvider(),
        forecast_provider=FakeForecastProvider(),
    )

    with pytest.raises(ServiceError) as exc_info:
        service.calculate_heatmap("aqi", 0)

    assert exc_info.value.code == "insufficient_spatial_data"
    assert exc_info.value.status_code == 503
    assert exc_info.value.details is not None
    assert exc_info.value.details["stations_usable"] == 0
    assert exc_info.value.details["stations_excluded"] == [
        "S01",
        "S02",
        "S03",
        "S04",
        "S05",
    ]


def test_real_station_service_strict_mode_does_not_replace_empty_database() -> None:
    station_service = StationService(
        StaticRowsDatabase([]),  # type: ignore[arg-type]
        stale_after_seconds=300,
    )

    service = SpatialDispersionService(
        station_service,
        weather_provider=FakeWeatherProvider(),
        forecast_provider=FakeForecastProvider(),
    )

    with pytest.raises(ServiceError) as exc_info:
        service.calculate_heatmap("aqi", 0)

    assert exc_info.value.code == "spatial_station_data_unavailable"
    assert exc_info.value.status_code == 503
    assert exc_info.value.details == {"upstream_code": "station_data_unavailable"}


def test_real_station_service_strict_mode_fails_closed_when_database_is_unavailable() -> None:
    station_service = StationService(Database(None), stale_after_seconds=300)

    service = SpatialDispersionService(
        station_service,
        weather_provider=FakeWeatherProvider(),
        forecast_provider=FakeForecastProvider(),
    )

    with pytest.raises(ServiceError) as exc_info:
        service.calculate_heatmap("aqi", 0)

    assert exc_info.value.code == "spatial_station_data_unavailable"
    assert exc_info.value.status_code == 503
    assert exc_info.value.details == {"upstream_code": "station_data_unavailable"}


def test_station_list_fails_closed_when_database_is_unavailable() -> None:
    station_service = StationService(Database(None), stale_after_seconds=300)

    with pytest.raises(ServiceError) as exc_info:
        station_service.list_stations()

    assert exc_info.value.code == "station_data_unavailable"
    assert exc_info.value.status_code == 503


@pytest.mark.parametrize("metric", ["aqi", "pm25", "co2", "noise_db", "temperature"])
def test_supported_metrics_produce_values_within_physical_range(metric: str) -> None:
    service = make_service()

    result = service.calculate_heatmap(metric, 0)

    minimum, maximum = service.METRIC_RANGES[metric]
    assert result["metric"] == metric
    assert all(minimum <= point["value"] <= maximum for point in result["grid_points"])


def test_invalid_metric_and_forecast_hour_are_rejected() -> None:
    service = make_service()

    with pytest.raises(ServiceError) as metric_error:
        service.calculate_heatmap("ozone", 0)
    with pytest.raises(ServiceError) as horizon_error:
        service.calculate_heatmap("aqi", 25)

    assert metric_error.value.code == "invalid_spatial_metric"
    assert metric_error.value.status_code == 422
    assert horizon_error.value.code == "invalid_spatial_forecast_hour"
    assert horizon_error.value.status_code == 422


def test_forecast_grid_uses_backend_forecasts_and_labels_assumptions() -> None:
    forecast = FakeForecastProvider()
    weather = FakeWeatherProvider(direction=None)
    service = make_service(weather=weather, forecast=forecast)

    result = service.calculate_heatmap("pm25", 6)

    assert len(forecast.calls) == 5
    assert all(call["history_points"] == 4 for call in forecast.calls)
    assert all(call["hours"] == 6 for call in forecast.calls)
    assert result["data_quality"]["forecast_sources"] == ["test_forecast_v1"]
    assert result["weather"]["wind_direction_deg"] == 135
    assert result["weather"]["assumptions"] == [
        "wind_direction_uses_documented_simulator_assumption",
        "current_wind_held_constant_for_forecast_horizon",
    ]
    assert all(item["forecast_source"] == "test_forecast_v1" for item in result["station_inputs"])


def test_station_with_insufficient_forecast_history_is_excluded() -> None:
    stations = make_stations()
    histories = make_histories(stations)
    histories["S05"] = histories["S05"][:2]
    station_service = FakeStationService(stations, histories)
    service = SpatialDispersionService(
        station_service,  # type: ignore[arg-type]
        weather_provider=FakeWeatherProvider(),
        forecast_provider=FakeForecastProvider(),
    )

    result = service.calculate_heatmap("aqi", 3)

    assert result["data_quality"]["stations_used"] == ["S01", "S02", "S03", "S04"]
    assert result["data_quality"]["exclusion_reasons"]["S05"] == [
        "insufficient_forecast_history"
    ]


def test_stale_weather_cannot_drive_spatial_model() -> None:
    service = make_service(weather=FakeWeatherProvider(is_stale=True))

    with pytest.raises(ServiceError) as exc_info:
        service.calculate_heatmap("aqi", 0)

    assert exc_info.value.code == "spatial_weather_stale"
    assert exc_info.value.status_code == 503


def test_agent_spatial_contract_accepts_grounded_response_and_rejects_nan() -> None:
    result = make_service().calculate_heatmap("aqi", 0)

    validated = SpatialAirQuality.model_validate(result)
    assert validated.data_quality.status == "valid"
    assert len(validated.grid_points) > 0

    invalid = dict(result)
    invalid["grid_points"] = [dict(result["grid_points"][0], value=float("nan"))]
    with pytest.raises(ValidationError):
        SpatialAirQuality.model_validate(invalid)


def test_spatial_api_returns_payload_and_structured_validation_error(monkeypatch) -> None:
    from backend.app import main as main_module

    monkeypatch.setattr(main_module, "spatial_service", make_service())
    client = TestClient(main_module.app)

    response, elapsed_ms = measure_best_ms(
        lambda: client.get(
            "/api/v1/spatial/heatmap",
            params={"metric": "aqi", "forecast_hour": 0},
            headers={"X-Request-ID": "spatial-api-test"},
        )
    )
    invalid = client.get(
        "/api/v1/spatial/heatmap",
        params={"metric": "ozone", "forecast_hour": 0},
        headers={"X-Request-ID": "spatial-api-invalid"},
    )

    assert response.status_code == 200
    assert elapsed_ms < 200, f"spatial API took {elapsed_ms:.2f} ms"
    assert response.json()["data_quality"]["status"] == "valid"
    assert invalid.status_code == 422
    assert invalid.json() == {
        "code": "invalid_spatial_metric",
        "message": "Unsupported spatial heatmap metric",
        "request_id": "spatial-api-invalid",
        "details": {
            "metric": "ozone",
            "allowed": ["aqi", "co2", "noise_db", "pm25", "temperature"],
        },
    }


@pytest.mark.asyncio
async def test_agent_graph_uses_real_spatial_http_endpoint(monkeypatch) -> None:
    from backend.app import main as main_module
    from src.agents.graph import build_graph
    from src.agents.tools.backend_client import BackendToolClient

    monkeypatch.setattr(main_module, "spatial_service", make_service())
    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://backend",
    ) as http_client:
        adapter = BackendToolClient("http://backend", client=http_client)
        result = await build_graph(adapter).ainvoke(
            {
                "query": (
                    "Khu vực quảng trường cá voi / hồ San Hô không khí thế nào "
                    "so với khu biển nước mặn?"
                ),
                "request_id": "spatial-real-http",
            }
        )

    assert result["used_tools"] == ["get_spatial_air_quality"]
    assert result["outcome"] == "answered"
    assert "Quảng trường Cá Voi" in result["answer"]
    assert "Công viên San Hô" in result["answer"]
    assert "Biển Hồ Nước Mặn" in result["answer"]
    assert "idw-dispersion-v2.0" in result["answer"]
    assert result["sources"][0]["source"] == "spatial_idw_dispersion_model"
    assert result["trace"]["tools"][0]["tool_name"] == "get_spatial_air_quality"
    assert result["trace"]["tools"][0]["status"] == "success"
