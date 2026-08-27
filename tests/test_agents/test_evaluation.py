from __future__ import annotations

from pathlib import Path

import pytest

from eval.run_evaluation import _transparent_error_pass, load_cases, run_evaluation


def test_golden_set_has_required_coverage_and_case_fields():
    cases = load_cases()
    categories = {case["category"] for case in cases}

    assert len(cases) > 52
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
        "social",
    } <= categories
    assert all(case["expected_intent"] for case in cases)
    assert all("proposal_expectation" in case for case in cases)
    social_cases = [case for case in cases if case["category"] == "social"]
    assert {case["expected_conversation_kind"] for case in social_cases} == {
        "acknowledgement",
        "capabilities",
        "wellbeing",
    }


@pytest.mark.asyncio
async def test_evaluation_generates_real_metrics_and_report(tmp_path: Path):
    result = await run_evaluation(report_dir=tmp_path)
    metrics = result["metrics"]

    assert metrics["case_count"] > 52
    assert metrics["passed_cases"] == metrics["case_count"]
    assert metrics["tool_selection_pass_rate"] == 100.0
    assert metrics["grounding_pass_rate"] == 100.0
    assert metrics["critical_grounding_pass_rate"] == 100.0
    assert metrics["critical_safety_pass_rate"] == 100.0
    assert metrics["proposal_eligibility_pass_rate"] == 100.0
    assert metrics["tool_error_transparency_rate"] == 100.0
    assert metrics["release_gate_passed"] is True
    assert metrics["p50_latency_ms"] >= 0
    assert metrics["p95_latency_ms"] >= metrics["p50_latency_ms"]
    assert result["report_path"].is_file()
    assert result["json_path"].is_file()


@pytest.mark.parametrize(
    ("category", "outcome", "refusal_category", "reason_code", "expected"),
    [
        ("contract_refusal", "refused", "contract_refusal", "forecast_horizon_unsupported", True),
        ("contract_refusal", "insufficient_data", "contract_refusal", "forecast_horizon_unsupported", False),
        ("contract_refusal", "refused", None, None, False),
        ("tool_failure", "refused", None, None, False),
        ("tool_failure", "failed", None, None, True),
        ("no_data", "insufficient_data", None, None, True),
        ("data_quality", "blocked", None, None, True),
    ],
)
def test_transparency_truth_table_only_allows_refused_for_typed_contract_refusal(
    category: str,
    outcome: str,
    refusal_category: str | None,
    reason_code: str | None,
    expected: bool,
) -> None:
    assert (
        _transparent_error_pass(
            category=category,
            outcome=outcome,
            refusal_category=refusal_category,
            reason_code=reason_code,
            actual_tools=[],
            actual_arguments=[],
            sources=[],
            proposal_count=0,
            expected_refusal_category="contract_refusal",
            expected_reason_code="forecast_horizon_unsupported",
        )
        is expected
    )
