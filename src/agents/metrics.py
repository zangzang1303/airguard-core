from __future__ import annotations

import math
from collections import Counter, deque
from collections.abc import Mapping
from threading import Lock
from typing import Any

_MAX_SAMPLES = 200
_lock = Lock()
_total = 0
_modes: Counter[str] = Counter()
_failures: Counter[str] = Counter()
_fallbacks = 0
_llm_calls = 0
_latencies: deque[float] = deque(maxlen=_MAX_SAMPLES)


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return round(ordered[index], 3)


def record_trace(trace: Mapping[str, Any]) -> None:
    global _fallbacks, _llm_calls, _total
    mode = str(trace.get("generation_mode") or "unknown")
    failure = trace.get("failure_code")
    latency = trace.get("latency_ms")
    with _lock:
        _total += 1
        _modes[mode] += 1
        call_count = trace.get("llm_call_count", 0)
        if isinstance(call_count, int) and call_count >= 0:
            _llm_calls += call_count
        if failure:
            _failures[str(failure)] += 1
            _fallbacks += 1
        if isinstance(latency, (int, float)):
            _latencies.append(float(latency))


def snapshot() -> dict[str, Any]:
    with _lock:
        total = _total
        modes = dict(_modes)
        failures = dict(_failures)
        fallback_count = _fallbacks
        llm_calls = _llm_calls
        latencies = list(_latencies)
    fallback_rate = round(fallback_count / total, 4) if total else 0.0
    p95 = _percentile(latencies, 0.95)
    alerts: list[str] = []
    if fallback_rate > 0:
        alerts.append("agent_fallback_detected")
    if p95 is not None and p95 >= 5000:
        alerts.append("agent_request_latency_demo_slo_breached")
    elif p95 is not None and p95 >= 2500:
        alerts.append("agent_request_latency_production_slo_breached")
    return {
        "total_requests": total,
        "generation_modes": modes,
        "llm_calls": llm_calls,
        "failure_codes": failures,
        "fallback_rate": fallback_rate,
        "latency_ms": {
            "sample_count": len(latencies),
            "p50": _percentile(latencies, 0.50),
            "p95": p95,
            "p99": _percentile(latencies, 0.99),
        },
        "alerts": alerts,
        "status": "ok" if not alerts else "attention",
    }
