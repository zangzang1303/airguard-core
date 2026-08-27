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
    assert result["answer"].count("fixture_forecast") == hours + 1  # points plus top-level provenance
    assert "không phải quan sát hiện tại" in result["answer"]
    assert "fixture_forecast" in result["answer"]
    assert all(source["station_id"] == "S01" for source in result["sources"])


@pytest.mark.asyncio
async def test_aqi_and_pm25_routes_preserve_metric_and_horizon():
    graph = build_graph(FakeBackendToolClient())

    aqi = await graph.ainvoke({"query": "AQI ở S03 trong 1 giờ tới dự báo thế nào?"})
    pm25 = await graph.ainvoke({"query": "PM2.5 S03 trong 3 giờ tới?"})

    assert aqi["used_tools"] == ["get_pm25_forecast"]
    assert "Dự báo AQI cho S03" in aqi["answer"]
    assert "µg/m³" not in aqi["answer"]
    assert pm25["used_tools"] == ["get_pm25_forecast"]
    assert "Dự báo PM25 cho S03" in pm25["answer"]
    assert pm25["answer"].count("fixture_forecast") == 4  # three points plus top-level provenance


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "Dự báo S01 trong 0 giờ tới?",
        "Dự báo S01 trong 4 giờ tới?",
        "Dự báo S01 trong 9 giờ tới?",
        "Dự báo PM2.5 S01 trong 13 giờ tới?",
        "Dự báo 24 giờ tới ở S01?",
        "Dự báo cả ngày ở S01?",
    ],
)
async def test_unsupported_forecast_horizon_is_contract_refusal_without_tool_call(query):
    result = await build_graph(FakeBackendToolClient()).ainvoke({"query": query})

    assert result["route"]["intent"] == "forecast"
    assert result["outcome"] == "refused"
    assert result["route"]["refusal_category"] == "contract_refusal"
    assert result["route"]["reason_code"] == "forecast_horizon_unsupported"
    assert result["used_tools"] == []
    assert result["route"]["tool_arguments"] == []
    assert result["sources"] == []
    assert result["trace"]["tools"] == []
    assert result["trace"]["refusal_category"] == "contract_refusal"
    assert result["trace"]["reason_code"] == "forecast_horizon_unsupported"
    assert "1–3 giờ" in result["answer"]
    assert "forecast" not in result["answer"].lower()
    assert "22.4" not in result["answer"]


@pytest.mark.asyncio
async def test_clock_time_forecast_requests_clarification_without_tool_call():
    result = await build_graph(FakeBackendToolClient()).ainvoke(
        {"query": "Dự báo PM2.5 S01 lúc 13 giờ"}
    )

    assert result["route"]["intent"] == "clarification"
    assert result["outcome"] == "clarification"
    assert result["used_tools"] == []


def test_forecast_assessment_preserves_backend_metadata():
    assessment = assess_forecast(
        {
            "station_id": "S01",
            "items": [{"hour": 1, "forecast_at": "2026-08-08T11:00:00+07:00", "value": 30.0, "confidence": 0.8, "source": "baseline-v1"}],
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
