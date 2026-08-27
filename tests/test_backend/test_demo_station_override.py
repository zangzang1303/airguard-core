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
