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


def test_evaluate_case_requires_live_provider_trace(monkeypatch):
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
                "answer": "PM2.5 grounded output",
                "used_tools": ["get_current_pm25"],
                "sources": [{"tool_name": "get_current_pm25", "token": "must-redact"}],
                "trace": {"generation_mode": "live_llm", "provider": "openai", "model": "test", "final_outcome": "answered"},
            },
            12.0,
        ),
    )

    result = module.evaluate_case(case, base_url="http://test/api/v1", user_id="user", timeout=1)

    assert result["result"] == "PASS"
    assert result["actual"]["sources"][0]["token"] == "[REDACTED]"


def test_evaluate_case_blocks_deterministic_fallback(monkeypatch):
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
                "trace": {"generation_mode": "deterministic_grounded", "final_outcome": "refused"},
            },
            12.0,
        ),
    )

    result = module.evaluate_case(case, base_url="http://test/api/v1", user_id="user", timeout=1)

    assert result["result"] == "FAIL"
    assert "generation_mode is not live_llm" in result["failure_reasons"]
