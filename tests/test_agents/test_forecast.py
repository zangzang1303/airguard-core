from __future__ import annotations

import pytest

from src.agents.graph import build_graph
from src.agents.policies.forecast_response import assess_forecast
from src.agents.response_composer import INSUFFICIENT_DATA_MESSAGE
from src.agents.tools.contracts import ToolEnvelope, ToolName
from src.agents.tools.fake_adapter import FakeBackendToolClient


@pytest.mark.parametrize("hours", [1, 2, 3])
@pytest.mark.asyncio
async def test_forecast_horizons_are_grounded_and_explicit(hours):
    graph = build_graph(FakeBackendToolClient())
    result = await graph.ainvoke({"query": f"Dự báo S01 trong {hours} giờ tới"})

    assert result["used_tools"] == ["get_pm25_forecast"]
    assert f"+{hours} giờ" in result["answer"]
    assert "không phải quan sát hiện tại" in result["answer"]
    assert "fixture_forecast" in result["answer"]
    assert all(source["station_id"] == "S01" for source in result["sources"])


def test_forecast_assessment_preserves_backend_metadata():
    assessment = assess_forecast(
        {
            "station_id": "S01",
            "items": [{"hour": 1, "pm25": 30.0, "confidence": 0.8, "source": "baseline-v1"}],
            "generated_at": "2026-08-08T10:00:00+07:00",
            "model_name": "moving-average-v1",
            "freshness": "fresh",
        }
    )

    assert assessment.generated_at == "2026-08-08T10:00:00+07:00"
    assert assessment.model_name == "moving-average-v1"
    assert assessment.freshness == "fresh"
    assert assessment.confidence_label == "high"
    assert assessment.limitations == ()


def test_low_confidence_forecast_is_marked_uncertain():
    assessment = assess_forecast(
        {
            "station_id": "S01",
            "items": [
                {"hour": 1, "pm25": 30.0, "confidence": 0.2, "source": "low-confidence-model"},
                {"hour": 2, "pm25": 60.0, "confidence": 0.2, "source": "low-confidence-model"},
            ],
        }
    )

    assert assessment.confidence_label == "low"
    assert assessment.trend == "uncertain"
    assert any("confidence thấp" in limitation for limitation in assessment.limitations)


class StaleForecastAdapter(FakeBackendToolClient):
    async def get_pm25_forecast(self, payload, request_id="fixture-request"):
        return ToolEnvelope(
            tool_name=ToolName.GET_PM25_FORECAST,
            request_id=request_id,
            data={
                "station_id": "S01",
                "items": [{"hour": 1, "pm25": 999, "confidence": 0.9, "source": "stale-model"}],
                "freshness": "stale",
            },
        )


@pytest.mark.asyncio
async def test_stale_forecast_is_blocked():
    graph = build_graph(StaleForecastAdapter())
    result = await graph.ainvoke({"query": "Dự báo S01 trong 1 giờ tới"})

    assert result["answer"] == INSUFFICIENT_DATA_MESSAGE
    assert result["sources"] == []
    assert "999" not in result["answer"]
