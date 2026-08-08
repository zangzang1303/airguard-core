from __future__ import annotations

from pathlib import Path

import pytest

from eval.run_evaluation import load_cases, run_evaluation


def test_golden_set_has_required_coverage_and_case_fields():
    cases = load_cases()
    categories = {case["category"] for case in cases}

    assert len(cases) >= 30
    assert {
        "current",
        "history",
        "compare",
        "weather",
        "forecast",
        "alert",
        "profile",
        "recommendation",
        "proposal",
        "no_data",
        "data_quality",
        "tool_failure",
        "injection",
        "medical_refusal",
        "device_refusal",
        "hitl_refusal",
    } <= categories
    assert all(case["expected_intent"] for case in cases)
    assert all("proposal_expectation" in case for case in cases)


@pytest.mark.asyncio
async def test_evaluation_generates_real_metrics_and_report(tmp_path: Path):
    result = await run_evaluation(report_dir=tmp_path)
    metrics = result["metrics"]

    assert metrics["case_count"] >= 30
    assert metrics["critical_grounding_pass_rate"] == 100.0
    assert metrics["critical_safety_pass_rate"] == 100.0
    assert metrics["proposal_eligibility_pass_rate"] == 100.0
    assert metrics["tool_error_transparency_rate"] == 100.0
    assert metrics["p50_latency_ms"] >= 0
    assert metrics["p95_latency_ms"] >= metrics["p50_latency_ms"]
    assert result["report_path"].is_file()
    assert result["json_path"].is_file()
