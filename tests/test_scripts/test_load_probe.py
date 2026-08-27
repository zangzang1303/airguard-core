from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _module():
    path = Path("eval/run_load_probe.py")
    spec = importlib.util.spec_from_file_location("run_load_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_percentile_uses_nearest_rank():
    module = _module()
    assert module.percentile([100, 200, 300, 400, 500], 0.95) == 500
    assert module.percentile([], 0.95) is None


def test_default_load_ceiling_is_five_seconds():
    module = _module()
    assert module.DEFAULT_MAX_P95_MS == 5000.0


def test_load_probe_requires_provider_free_deterministic_chat() -> None:
    module = _module()
    results = [
        {"generation_mode": "deterministic_grounded", "llm_call_count": 0, "http_status": 200, "request_latency_ms": 12.0}
    ]
    deterministic = [item for item in results if item["generation_mode"] == "deterministic_grounded"]
    unexpected_llm = [item for item in results if item["llm_call_count"] != 0]

    assert len(deterministic) == len(results)
    assert not unexpected_llm
