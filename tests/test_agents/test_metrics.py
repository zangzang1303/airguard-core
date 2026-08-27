from __future__ import annotations

import importlib


def _fresh_module():
    import src.agents.metrics as metrics

    return importlib.reload(metrics)


def test_metrics_are_aggregate_and_raise_latency_and_fallback_alerts():
    metrics = _fresh_module()
    metrics.record_trace(
        {
            "generation_mode": "deterministic_grounded",
            "llm_call_count": 1,
            "llm_stage": "semantic_router",
            "latency_ms": 2600,
            "request_id": "hidden",
        }
    )
    metrics.record_trace(
        {
            "generation_mode": "deterministic_grounded",
            "latency_ms": 5100,
            "failure_code": "provider_deadline_exceeded",
            "query": "must not appear",
        }
    )

    result = metrics.snapshot()

    assert result["total_requests"] == 2
    assert result["llm_calls"] == 1
    assert result["fallback_rate"] == 0.5
    assert result["latency_ms"]["p95"] == 5100
    assert "agent_fallback_detected" in result["alerts"]
    assert "agent_request_latency_demo_slo_breached" in result["alerts"]
    assert "request_id" not in result
    assert "query" not in result


def test_expected_deterministic_social_response_is_not_a_provider_fallback():
    metrics = _fresh_module()
    metrics.record_trace(
        {
            "generation_mode": "deterministic_grounded",
            "conversation_mode": "deterministic_social",
            "latency_ms": 1,
        }
    )

    result = metrics.snapshot()

    assert result["fallback_rate"] == 0.0
    assert result["llm_calls"] == 0
    assert "agent_fallback_detected" not in result["alerts"]
