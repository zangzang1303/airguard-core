from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.services.clean_running_route_service import CleanRunningRouteService
from backend.app.services.database import ServiceError
from backend.app.services.inhaled_dose_service import InhaledDoseService, calculate_estimated_inhaled_mass
from backend.app.services.predictive_warning_email import (
    build_predictive_warning_deep_link,
    render_predictive_warning_email,
)
from backend.app.services.predictive_warning_service import (
    PredictiveWarningNotificationService,
    PredictiveWarningService,
)
from backend.app.services.road_graph_router import road_graph_router

NOW = datetime(2026, 8, 29, 4, 0, tzinfo=UTC)


class FakeStationService:
    def __init__(self, stations: list[dict] | None = None) -> None:
        coordinates = road_graph_router.STATION_COORDINATES
        self.stations = stations or [
            {
                "station_id": station_id,
                "latitude": lat,
                "longitude": lon,
                "pm25": 20.0 + index * 10,
                "status": "online",
                "freshness": "fresh",
                "is_stale": False,
                "source": "simulator",
                "updated_at": NOW.isoformat(),
            }
            for index, (station_id, (lat, lon)) in enumerate(coordinates.items())
        ]

    def list_stations(self, *args, **kwargs):
        return deepcopy(self.stations)

    def get_station(self, station_id: str):
        return next(deepcopy(item) for item in self.stations if item["station_id"] == station_id)

    def get_forecast_history(self, station_id: str):
        current = self.get_station(station_id)["pm25"]
        return [
            {"measured_at": (NOW - timedelta(minutes=20 - index * 10)).isoformat(), "pm25": current + index}
            for index in range(3)
        ]


def test_inhaled_mass_fixture_ratio_and_boundaries() -> None:
    assert float(calculate_estimated_inhaled_mass(pm25_ug_m3=42.5, activity="running", duration_minutes=30)) == 57.375
    resting = calculate_estimated_inhaled_mass(pm25_ug_m3=42.5, activity="resting", duration_minutes=30)
    running = calculate_estimated_inhaled_mass(pm25_ug_m3=42.5, activity="running", duration_minutes=30)
    assert running / resting == pytest.approx(7.5)
    for duration in (1, 180):
        assert calculate_estimated_inhaled_mass(pm25_ug_m3=1, activity="running", duration_minutes=duration) > 0
    for duration in (0, 181):
        with pytest.raises(ServiceError) as error:
            calculate_estimated_inhaled_mass(pm25_ug_m3=1, activity="running", duration_minutes=duration)
        assert error.value.code == "invalid_duration"


@pytest.mark.parametrize("status,freshness,is_stale", [("offline", "fresh", False), ("online", "stale", True), ("invalid", "fresh", False)])
def test_inhaled_mass_rejects_bad_current_quality(status: str, freshness: str, is_stale: bool) -> None:
    station = FakeStationService().stations[0]
    station.update({"status": status, "freshness": freshness, "is_stale": is_stale})
    service = InhaledDoseService(FakeStationService([station]), clock=lambda: NOW)
    with pytest.raises(ServiceError) as error:
        service.estimate(station_id="S01", activity="running", duration_minutes=30)
    assert error.value.code == "environmental_data_unavailable"


def test_measurement_timestamp_gate_rejects_fresh_heartbeat_with_stale_pm25() -> None:
    stations = FakeStationService().stations
    for station in stations:
        station["updated_at"] = (NOW - timedelta(seconds=301)).isoformat()

    with pytest.raises(ServiceError) as dose_error:
        InhaledDoseService(FakeStationService(stations), clock=lambda: NOW).estimate(
            station_id="S01",
            activity="running",
            duration_minutes=30,
        )
    assert dose_error.value.code == "environmental_data_unavailable"

    with pytest.raises(ServiceError) as route_error:
        CleanRunningRouteService(FakeStationService(stations), clock=lambda: NOW).recommend(
            origin={"lat": 20.9938, "lon": 105.9485, "source": "map_selection"},
            target_distance_km=3,
        )
    assert route_error.value.code == "insufficient_route_coverage"


def test_inhaled_mass_exact_response_is_not_absorbed_dose() -> None:
    station = FakeStationService().stations[0]
    station["pm25"] = 42.5
    result = InhaledDoseService(FakeStationService([station]), clock=lambda: NOW).estimate(
        station_id="S01", activity="running", duration_minutes=30
    )
    assert result["estimated_inhaled_mass_ug"] == 57.38
    assert "hấp thụ" in result["disclaimer"]
    assert "cigarette" not in str(result).lower()


def test_clean_route_is_graph_grounded_deterministic_and_segment_totals_match() -> None:
    service = CleanRunningRouteService(FakeStationService(), clock=lambda: NOW)
    request = {
        "origin": {"lat": 20.9938, "lon": 105.9485, "source": "demo_default"},
        "target_distance_km": 3.0,
        "pace_minutes_per_km": 6.5,
        "data_mode": "current",
        "forecast_hour": None,
    }
    first = service.recommend(**request)
    second = service.recommend(**request)
    assert first["route_id"] == second["route_id"]
    assert first["graph"]["graph_source"] == "curated_demo_graph"
    assert all(segment["edge_id"] for segment in first["segments"])
    assert max(segment["distance_m"] for segment in first["segments"]) <= 35.01
    assert sum(segment["estimated_inhaled_mass_ug"] for segment in first["segments"]) == pytest.approx(
        first["estimated_inhaled_mass_ug"], abs=0.01
    )
    assert sum(segment["duration_minutes"] for segment in first["segments"]) == pytest.approx(
        first["duration_minutes"], abs=0.01
    )


def test_clean_route_requires_three_quality_stations_and_valid_origin() -> None:
    service = CleanRunningRouteService(FakeStationService(FakeStationService().stations[:2]), clock=lambda: NOW)
    with pytest.raises(ServiceError) as error:
        service.recommend(
            origin={"lat": 20.9938, "lon": 105.9485, "source": "map_selection"},
            target_distance_km=3,
        )
    assert error.value.code == "insufficient_route_coverage"
    with pytest.raises(ServiceError) as error:
        CleanRunningRouteService(FakeStationService(), clock=lambda: NOW).recommend(
            origin={"lat": 21.2, "lon": 106.2, "source": "gps"},
            target_distance_km=3,
        )
    assert error.value.code == "route_origin_out_of_bounds"


def test_clean_route_contract_boundaries_and_non_finite_values() -> None:
    validate = CleanRunningRouteService._validate_request
    for target in (1, 10):
        for pace in (3, 20):
            assert validate(
                {"lat": 20.9938, "lon": 105.9485, "source": "map_selection"},
                target,
                pace,
                "current",
                None,
            )[2] == "map_selection"
    for target in (0.99, 10.01, float("nan"), float("inf")):
        with pytest.raises(ServiceError) as error:
            validate(
                {"lat": 20.9938, "lon": 105.9485, "source": "map_selection"},
                target,
                6.5,
                "current",
                None,
            )
        assert error.value.code == "route_target_out_of_range"

    service = CleanRunningRouteService(FakeStationService(), clock=lambda: NOW)
    for target in (1, 10):
        route = service.recommend(
            origin={"lat": 20.9938, "lon": 105.9485, "source": "demo_default"},
            target_distance_km=target,
            pace_minutes_per_km=6.5,
        )
        assert abs(route["distance_km"] - target) / target <= 0.20
        assert all(segment["edge_id"] for segment in route["segments"])


class FakeAudit:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def record(self, **kwargs) -> None:
        self.rows.append(kwargs)


class FakeEpisodeRepository:
    def __init__(self) -> None:
        self.active: dict | None = None
        self.actual_alert = False
        self.transitions: list[str] = []

    def get_active_episode(self, station_id, rule):
        return deepcopy(self.active)

    def has_active_pm25_alert(self, station_id):
        return self.actual_alert

    def upsert_active_episode(self, candidate):
        if self.active is None:
            self.active = {"episode_id": str(uuid4()), "status": "active", "clear_evaluation_count": 0, **candidate}
        else:
            episode_id = self.active["episode_id"]
            self.active = {**self.active, **candidate, "episode_id": episode_id, "clear_evaluation_count": 0}
        return deepcopy(self.active)

    def increment_clear(self, episode_id):
        self.active["clear_evaluation_count"] += 1
        return deepcopy(self.active)

    def transition_episode(self, episode_id, status):
        self.active["status"] = status
        self.transitions.append(status)
        row = deepcopy(self.active)
        self.active = None
        return row


def qualifying_forecast(history, hours, metric, generated_at):
    return {
        "freshness": "fresh",
        "generated_at": generated_at.isoformat(),
        "confidence": 0.8,
        "source": "simulator_history_damped_linear_v1",
        "model_version": "damped_linear_trend_v1",
        "items": [
            {
                "hour_offset": 1,
                "forecast_at": (generated_at + timedelta(minutes=45)).isoformat(),
                "value": 65,
                "value_min": 55,
                "value_max": 75,
                "confidence": 0.8,
                "source": "simulator_history_damped_linear_v1",
            }
        ],
    }


def no_crossing_forecast(history, hours, metric, generated_at):
    result = qualifying_forecast(history, hours, metric, generated_at)
    result["items"][0].update({"value": 40, "value_min": 35, "value_max": 45})
    return result


def rolling_two_hour_forecast(history, hours, metric, generated_at):
    result = qualifying_forecast(history, hours, metric, generated_at)
    result["items"][0].update(
        {
            "hour_offset": 2,
            "forecast_at": (generated_at + timedelta(minutes=120)).isoformat(),
        }
    )
    return result


def test_predictive_dry_run_never_persists_or_enqueues_and_actual_alert_is_observed() -> None:
    repo = FakeEpisodeRepository()
    audit = FakeAudit()
    service = PredictiveWarningService(
        repo,
        FakeStationService(),
        audit,
        clock=lambda: NOW,
        forecast_fn=qualifying_forecast,
    )
    result = service.evaluate("S01", dry_run=True, correlation_id="test")
    assert result["outcome"] == "candidate"
    assert result["notification_enqueued"] is False
    assert repo.active is None

    repo.upsert_active_episode(result["candidate"])
    repo.actual_alert = True
    dry_result = service.evaluate("S01", dry_run=True, correlation_id="test")
    assert dry_result["reason_code"] == "actual_alert_active"
    assert repo.transitions == []
    live_result = service.evaluate("S01", dry_run=False, correlation_id="test")
    assert live_result["reason_code"] == "actual_alert_active"
    assert repo.transitions == ["observed"]


def test_predictive_requires_two_clear_evaluations() -> None:
    repo = FakeEpisodeRepository()
    service = PredictiveWarningService(
        repo,
        FakeStationService(),
        FakeAudit(),
        clock=lambda: NOW,
        forecast_fn=qualifying_forecast,
    )
    candidate = service.evaluate("S01", dry_run=True, correlation_id="test")["candidate"]
    repo.upsert_active_episode(candidate)
    service._forecast = no_crossing_forecast
    first = service.evaluate("S01", dry_run=False, correlation_id="test")
    second = service.evaluate("S01", dry_run=False, correlation_id="test")
    assert first["outcome"] == "clearing"
    assert second["outcome"] == "resolved"


def test_predictive_episode_keeps_original_target_until_lead_window() -> None:
    repo = FakeEpisodeRepository()
    clock = {"now": NOW}

    class Notifier:
        calls = 0

        def enqueue(self, episode, correlation_id):
            self.calls += 1
            return {"enqueued": 1, "reused": 0, "failed": 0, "reason_code": None}

    notifier = Notifier()
    station_service = FakeStationService()
    service = PredictiveWarningService(
        repo,
        station_service,
        FakeAudit(),
        notifier=notifier,
        clock=lambda: clock["now"],
        forecast_fn=rolling_two_hour_forecast,
    )
    first = service.evaluate("S01", dry_run=False, correlation_id="first")
    original_target = first["episode"]["forecast_target_at"]
    assert first["notification"]["reason_code"] == "outside_lead_window"

    clock["now"] = NOW + timedelta(minutes=60)
    for station in station_service.stations:
        station["updated_at"] = clock["now"].isoformat()
    second = service.evaluate("S01", dry_run=False, correlation_id="second")
    assert second["episode"]["forecast_target_at"] == original_target
    assert second["notification"]["enqueued"] == 1
    assert notifier.calls == 1


def test_predictive_rejects_low_confidence_and_stale_forecast() -> None:
    def bad_forecast(history, hours, metric, generated_at):
        result = qualifying_forecast(history, hours, metric, generated_at)
        result["confidence"] = 0.59
        return result

    service = PredictiveWarningService(
        FakeEpisodeRepository(),
        FakeStationService(),
        FakeAudit(),
        clock=lambda: NOW,
        forecast_fn=bad_forecast,
    )
    assert service.evaluate("S01", dry_run=True, correlation_id="test")["reason_code"] == "insufficient_forecast_quality"

    def stale_forecast(history, hours, metric, generated_at):
        result = qualifying_forecast(history, hours, metric, generated_at)
        result["generated_at"] = (generated_at - timedelta(seconds=901)).isoformat()
        return result

    service._forecast = stale_forecast
    assert service.evaluate("S01", dry_run=True, correlation_id="test")["reason_code"] == "insufficient_forecast_quality"

    stations = FakeStationService().stations
    stations[0]["updated_at"] = (NOW - timedelta(seconds=301)).isoformat()
    stale_measurement_service = PredictiveWarningService(
        FakeEpisodeRepository(),
        FakeStationService(stations),
        FakeAudit(),
        clock=lambda: NOW,
        forecast_fn=qualifying_forecast,
    )
    assert (
        stale_measurement_service.evaluate("S01", dry_run=True, correlation_id="test")["reason_code"]
        == "environmental_data_unavailable"
    )


def test_notification_idempotency_key_prevents_duplicate_enqueue() -> None:
    class RecipientRepo:
        def list_predictive_recipients(self):
            return [{"user_id": "u1", "email": "resident@example.invalid"}]

    class Task:
        calls: list[dict] = []

        @classmethod
        def apply_async(cls, **kwargs):
            cls.calls.append(kwargs)

    jobs: dict[str, dict] = {}

    def reserve(task_id, job_type, key, payload):
        if key in jobs:
            return jobs[key], False
        jobs[key] = {"task_id": task_id, "status": "PENDING"}
        return jobs[key], True

    notifier = PredictiveWarningNotificationService(
        RecipientRepo(),
        FakeAudit(),
        notification_task=Task,
        enabled=True,
        reserve_job_fn=reserve,
        mark_job_failed_fn=lambda *args, **kwargs: None,
    )
    episode = {"episode_id": str(uuid4()), "severity": "warning"}
    first = notifier.enqueue(episode, "test")
    second = notifier.enqueue(episode, "test")
    assert first["enqueued"] == 1
    assert second["reused"] == 1
    assert len(Task.calls) == 1


def test_email_deep_link_is_closed_and_template_escapes_dynamic_content() -> None:
    episode_id = str(uuid4())
    link = build_predictive_warning_deep_link(
        frontend_url="http://localhost:5173?return_url=https://evil.example",
        station_id="S01",
        episode_id=episode_id,
    )
    assert link == f"http://localhost:5173/?panel=alerts&station_id=S01&predictive_warning_id={episode_id}"
    episode = {
        "episode_id": episode_id,
        "station_id": "S01",
        "severity": "warning",
        "predicted_value": "<script>",
        "predicted_min": 50,
        "predicted_max": 70,
        "confidence": 0.8,
        "forecast_target_at": NOW.isoformat(),
        "model_version": "demo-model",
        "policy_version": "demo-policy",
        "source": "simulator<script>",
    }
    rendered = render_predictive_warning_email(episode, frontend_url="http://localhost:5173")
    assert "<script>" not in rendered["html"]
    assert "&lt;script&gt;" in rendered["html"]
    assert "Xem Bản Đồ Trực Tiếp" in rendered["html"]
    assert "Checklist Hành Động" in rendered["html"]
    assert link in rendered["text"]


def test_agent_route_reuses_canonical_service_without_recomputing_geometry() -> None:
    from backend.app.services.geospatial_agent_service import GeospatialAgentService

    expected_route = {
        "route_id": "route-policy-v1:fixture",
        "distance_km": 3.01,
        "duration_minutes": 19.57,
        "estimated_inhaled_mass_ug": 41.23,
        "exposure_reduction_pct": None,
        "coordinates": [[20.9938, 105.9485], [20.994, 105.949]],
        "segments": [
            {
                "edge_id": "E1",
                "coordinates": [[20.9938, 105.9485], [20.994, 105.949]],
                "distance_m": 30,
                "duration_minutes": 0.2,
                "pm25": 30,
                "level": "moderate",
                "estimated_inhaled_mass_ug": 0.27,
                "source_station_ids": ["S01", "S02", "S03"],
                "observed_at": NOW.isoformat(),
                "source": "spatial_idw_route_segment",
            }
        ],
        "data_mode": "current",
        "graph": {"graph_source": "curated_demo_graph"},
        "assumptions": [],
        "disclaimer": "Tuyến demo; tự kiểm tra điều kiện đường thực tế.",
    }

    class FakeCanonicalRoute:
        calls: list[dict] = []

        def recommend(self, **kwargs):
            self.calls.append(kwargs)
            return deepcopy(expected_route)

    canonical = FakeCanonicalRoute()
    snapshots = {}
    for item in FakeStationService().stations:
        snapshots[item["station_id"]] = {
            **item,
            "aqi": 50,
            "co2": 500,
            "noise_db": 55,
            "temperature": 28,
        }
    result = GeospatialAgentService(clean_route_service=canonical).process_query(
        "Gợi ý tuyến chạy bộ 3 km",
        map_context={"selected_origin": {"lat": 20.9938, "lng": 105.9485, "source": "map_selection"}},
        station_snapshots=snapshots,
        station_histories={},
    )
    assert len(canonical.calls) == 1
    assert result["route"] == expected_route
    route_action = next(item for item in result["map_actions"] if item["type"] == "highlight_route")
    assert route_action["coordinates"] == expected_route["coordinates"]
    assert route_action["estimated_inhaled_mass_ug"] == expected_route["estimated_inhaled_mass_ug"]
    assert "hấp thụ" not in result["response"].lower()


def test_agent_route_service_failure_fails_closed_without_numbers_or_geometry() -> None:
    from backend.app.services.geospatial_agent_service import GeospatialAgentService

    snapshots = {
        item["station_id"]: {
            **item,
            "aqi": 50,
            "co2": 500,
            "noise_db": 55,
            "temperature": 28,
        }
        for item in FakeStationService().stations
    }
    result = GeospatialAgentService().process_query(
        "Gợi ý tuyến chạy bộ 3 km",
        map_context={"selected_origin": {"lat": 20.9938, "lng": 105.9485, "source": "map_selection"}},
        station_snapshots=snapshots,
        station_histories={},
    )
    assert result["intent"] == "insufficient_data"
    assert result["error"]["code"] == "insufficient_route_coverage"
    assert result["evidence"] == []
    assert all(action["type"] != "highlight_route" for action in result["map_actions"])
    assert "estimated_inhaled_mass_ug" not in result


def test_api_preferences_require_session_and_csrf_and_reject_unknown_fields(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from backend.app import main as main_module
    from backend.app.dependencies.auth import get_current_user

    class FakePreferences:
        def get(self, user_id):
            return {"environmental_email_enabled": False, "predictive_email_enabled": False}

        def update(self, **kwargs):
            return kwargs["values"]

    monkeypatch.setattr(main_module, "notification_preference_service", FakePreferences())
    client = TestClient(main_module.app)
    unauthenticated = client.get("/api/v1/auth/notification-preferences")
    assert unauthenticated.status_code == 401

    main_module.app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "00000000-0000-0000-0000-000000000101",
        "role": "resident",
    }
    try:
        client.cookies.set("airguard_session", "session-value")
        no_csrf = client.patch(
            "/api/v1/auth/notification-preferences",
            json={"predictive_email_enabled": True},
        )
        assert no_csrf.status_code == 403
        client.cookies.set("airguard_csrf", "csrf-value")
        unknown = client.patch(
            "/api/v1/auth/notification-preferences",
            json={"predictive_email_enabled": True, "return_url": "https://evil.example"},
            headers={"X-CSRF-Token": "csrf-value"},
        )
        assert unknown.status_code == 422
        accepted = client.patch(
            "/api/v1/auth/notification-preferences",
            json={"predictive_email_enabled": True},
            headers={"X-CSRF-Token": "csrf-value"},
        )
        assert accepted.status_code == 200
        assert accepted.json()["preferences"] == {"predictive_email_enabled": True}
    finally:
        main_module.app.dependency_overrides.clear()


def test_predictive_evaluate_requires_manager_and_csrf(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from backend.app import main as main_module
    from backend.app.dependencies.auth import require_manager

    class FakePredictive:
        def evaluate(self, station_id, *, dry_run, correlation_id):
            return {"outcome": "candidate", "dry_run": dry_run, "notification_enqueued": False}

    monkeypatch.setattr(main_module, "predictive_warning_service", FakePredictive())
    client = TestClient(main_module.app)
    forbidden = client.post(
        "/api/v1/predictive-warnings/evaluate",
        json={"station_id": "S01", "dry_run": True},
    )
    assert forbidden.status_code == 401

    main_module.app.dependency_overrides[require_manager] = lambda: {
        "user_id": "00000000-0000-0000-0000-000000000201",
        "role": "manager",
    }
    try:
        client.cookies.set("airguard_session", "session-value")
        no_csrf = client.post(
            "/api/v1/predictive-warnings/evaluate",
            json={"station_id": "S01", "dry_run": True},
        )
        assert no_csrf.status_code == 403
        client.cookies.set("airguard_csrf", "csrf-value")
        response = client.post(
            "/api/v1/predictive-warnings/evaluate",
            json={"station_id": "S01", "dry_run": True},
            headers={"X-CSRF-Token": "csrf-value"},
        )
        assert response.status_code == 200
        assert response.json()["notification_enqueued"] is False
    finally:
        main_module.app.dependency_overrides.clear()


def test_predictive_worker_revalidates_before_provider_and_retries_transient_failure(monkeypatch) -> None:
    from types import SimpleNamespace

    from backend.app.services.resend_email_provider import EmailDeliveryResult
    from backend.app.tasks import predictive_warning_tasks as task_module
    from backend.app.tasks.task_support import TransientTaskError

    episode_id = str(uuid4())
    episode = {
        "episode_id": episode_id,
        "station_id": "S01",
        "severity": "warning",
        "predicted_value": 65,
        "predicted_min": 55,
        "predicted_max": 75,
        "confidence": 0.8,
        "forecast_target_at": (NOW + timedelta(minutes=45)).isoformat(),
        "model_version": "damped_linear_trend_v1",
        "policy_version": "predictive-warning-policy-v1",
        "source": "simulator_history_damped_linear_v1",
    }

    class Service:
        calls = 0

        def revalidate_for_delivery(self, requested_episode_id, recipient_user_id):
            self.calls += 1
            assert requested_episode_id == episode_id
            return episode, {"user_id": recipient_user_id, "email": "resident@example.invalid"}

    service = Service()
    audit = FakeAudit()
    monkeypatch.setattr(
        task_module,
        "_services",
        lambda notification_task=None: (
            SimpleNamespace(frontend_url="http://localhost:5173"),
            SimpleNamespace(mark_notified=lambda value: None),
            audit,
            service,
        ),
    )
    monkeypatch.setattr(task_module, "run_idempotent", lambda **kwargs: kwargs["operation"]())
    monkeypatch.setattr(
        task_module.ResendEmailProvider,
        "send",
        lambda self, **kwargs: EmailDeliveryResult(
            status="failed",
            provider="resend",
            reason_code="provider_timeout",
            retryable=True,
        ),
    )
    with pytest.raises(TransientTaskError):
        task_module.send_predictive_warning_notification.run(
            episode_id=episode_id,
            recipient_user_id="resident-1",
            idempotency_key=f"predictive-warning:{episode_id}:warning:resident-1",
        )
    assert service.calls == 1


def test_schema_defaults_preferences_to_opt_out_and_enforces_one_active_episode() -> None:
    from pathlib import Path

    migration = Path("backend/db/migrations/20260829_006_personalized_alerts.sql").read_text(encoding="utf-8")
    normalized = " ".join(migration.lower().split())
    assert "environmental_email_enabled boolean not null default false" in normalized
    assert "predictive_email_enabled boolean not null default false" in normalized
    assert "create unique index if not exists uq_predictive_warning_active_episode" in normalized
    assert "where status = 'active'" in normalized
