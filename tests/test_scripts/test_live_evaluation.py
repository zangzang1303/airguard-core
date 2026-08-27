from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _module():
    path = Path("eval/run_live_evaluation.py")
    spec = importlib.util.spec_from_file_location("run_live_evaluation", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_live_cases_cover_the_five_required_gate_cases():
    module = _module()
    assert [case.case_id for case in module.LIVE_CASES] == ["LIVE-01", "LIVE-02", "LIVE-03", "LIVE-04", "LIVE-05"]


def test_evaluate_case_requires_deterministic_provider_free_trace(monkeypatch):
    module = _module()
    case = module.LIVE_CASES[0]
    request_id = "live-eval-live-01-fixed"

    monkeypatch.setattr(module.uuid, "uuid4", lambda: "fixed")
    monkeypatch.setattr(
        module,
        "_post_json",
        lambda *_args, **_kwargs: (
            200,
            {
                "request_id": request_id,
                "answer": "PM2.5 tại S01, nguồn simulator, dữ liệu mô phỏng.",
                "used_tools": ["get_current_pm25"],
                "sources": [{"tool_name": "get_current_pm25", "token": "must-redact"}],
                "trace": {"generation_mode": "deterministic_grounded", "llm_call_count": 0, "final_outcome": "answered"},
            },
            12.0,
        ),
    )

    result = module.evaluate_case(case, base_url="http://test/api/v1", user_id="user", timeout=1)

    assert result["result"] == "PASS"
    assert result["actual"]["sources"][0]["token"] == "[REDACTED]"


def test_evaluate_case_reads_backend_proxy_answer_shape(monkeypatch):
    module = _module()
    case = module.LIVE_CASES[0]
    monkeypatch.setattr(module.uuid, "uuid4", lambda: "fixed")
    monkeypatch.setattr(
        module,
        "_post_json",
        lambda *_args, **_kwargs: (
            200,
            {
                "request_id": "live-eval-live-01-fixed",
                "answer": {
                    "summary": "PM2.5 tại S01, nguồn simulator, dữ liệu mô phỏng.",
                    "details": "",
                },
                "used_tools": ["get_current_pm25"],
                "sources": [{"tool_name": "get_current_pm25"}],
                "trace": {
                    "generation_mode": "deterministic_grounded",
                    "llm_call_count": 0,
                    "final_outcome": "answered",
                },
            },
            12.0,
        ),
    )

    result = module.evaluate_case(case, base_url="http://test/api/v1", user_id="user", timeout=1)

    assert result["result"] == "PASS"
    assert result["actual"]["output"].startswith("PM2.5 tại S01")


def test_evaluate_case_blocks_unexpected_provider_call(monkeypatch):
    module = _module()
    case = module.LIVE_CASES[4]
    monkeypatch.setattr(module.uuid, "uuid4", lambda: "fixed")
    monkeypatch.setattr(
        module,
        "_post_json",
        lambda *_args, **_kwargs: (
            200,
            {
                "request_id": "live-eval-live-05-fixed",
                "answer": "Mình không thể thực hiện yêu cầu này.",
                "used_tools": [],
                "sources": [],
                "trace": {"generation_mode": "deterministic_grounded", "llm_call_count": 1, "final_outcome": "refused"},
            },
            12.0,
        ),
    )

    result = module.evaluate_case(case, base_url="http://test/api/v1", user_id="user", timeout=1)

    assert result["result"] == "FAIL"
    assert "llm_call_count expected 0, got 1" in result["failure_reasons"]


def test_p95_uses_nearest_rank_and_enforces_worst_of_five():
    module = _module()

    assert module._p95([100, 200, 300, 400, 500]) == 500
    assert module._p95([]) is None


def test_release_result_distinguishes_demo_limitations_from_production_target():
    module = _module()
    cases = [{"result": "PASS"}] * 5

    assert module._release_result(cases, 2400.0, 5000.0) == "PASS"
    assert module._release_result(cases, 3200.0, 5000.0) == "PASS WITH LIMITATIONS"
    assert module._release_result(cases, 5200.0, 5000.0) == "BLOCKED"
    assert module._release_result([{ "result": "FAIL" }] + cases[1:], 3200.0, 5000.0) == "BLOCKED"


def test_legacy_expected_provider_argument_does_not_reintroduce_chat_probe(monkeypatch):
    module = _module()
    case = module.LIVE_CASES[0]
    monkeypatch.setattr(module.uuid, "uuid4", lambda: "fixed")
    monkeypatch.setattr(
        module,
        "_post_json",
        lambda *_args, **_kwargs: (
            200,
            {
                "request_id": "live-eval-live-01-fixed",
                "answer": "PM2.5 tại S01, nguồn simulator, dữ liệu mô phỏng.",
                "used_tools": ["get_current_pm25"],
                "sources": [{"tool_name": "get_current_pm25"}],
                "trace": {
                    "generation_mode": "deterministic_grounded",
                    "llm_call_count": 0,
                    "final_outcome": "answered",
                },
            },
            12.0,
        ),
    )

    result = module.evaluate_case(
        case,
        base_url="http://test/api/v1",
        user_id="user",
        timeout=1,
        expected_provider="agentrouter",
    )

    assert result["result"] == "PASS"
    assert result["actual"]["llm_call_count"] == 0
