from __future__ import annotations

from datetime import datetime

from backend.app.services.live_telemetry_engine import LiveTelemetryEngine


def test_demo_override_persists_over_automatic_ticks_and_can_be_cleared():
    engine = LiveTelemetryEngine()
    station = engine.set_demo_override(
        "S03", {"pm25": 120.0, "co2": 1600.0, "noise_db": 88.0, "temperature": 39.0}
    )

    assert station["demo_override"] is True
    assert station["pm25"] == 120.0
    assert station["aqi"] > 150
    evidence = engine.get_demo_override_evidence("S03")
    assert evidence is not None
    assert evidence["source"] == "demo_override"
    assert isinstance(evidence["started_at"], datetime)

    engine.tick()
    assert engine.get_latest("S03")["pm25"] == 120.0

    engine.clear_demo_override("S03")
    assert "demo_override" not in engine.get_latest("S03")
    assert engine.get_demo_override_evidence("S03") is None


def test_demo_override_tick_evaluates_alerts_and_uses_the_normal_hitl_side_effects(monkeypatch) -> None:
    """Overrides bypass MQTT by design, but must not bypass alert/HITL evaluation."""
    from backend.app import main as main_module

    class FakeEngine:
        def get_demo_overrides(self):
            return {"S02": {"pm25": 120.0}}

    class FakeAlerts:
        def evaluate_station_with_alerts(self, station_id, *, correlation_id):
            assert station_id == "S02"
            assert correlation_id.startswith("demo-override:S02:")
            return {"station_id": station_id, "status": "active"}, [{"alert_id": "alert-1"}]

    observed: list[tuple[dict, list[dict], str]] = []

    monkeypatch.setattr(main_module, "live_engine", FakeEngine())
    monkeypatch.setattr(main_module, "alert_engine", FakeAlerts())
    monkeypatch.setattr(
        main_module,
        "_run_alert_side_effects",
        lambda primary, alerts, correlation_id: observed.append((primary, alerts, correlation_id)),
    )

    main_module._evaluate_demo_override_alerts()

    assert observed[0][0]["station_id"] == "S02"
    assert observed[0][1] == [{"alert_id": "alert-1"}]
