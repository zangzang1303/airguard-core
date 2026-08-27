"""Small, bounded staging load probe for the canonical Agent chat endpoint."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000101"
DEFAULT_MAX_P95_MS = 5000.0
MESSAGES = (
    "PM2.5 hiện tại ở S01 thế nào?",
    "So sánh S01 và S02 hiện tại.",
    "Tôi có nên chạy bộ ngoài trời tại S01 trong 3 giờ tới không?",
)


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return round(ordered[index], 3)


def run_one(base_url: str, user_id: str, message: str, timeout: float) -> dict[str, object]:
    request_id = f"load-probe-{uuid.uuid4()}"
    payload = json.dumps({"message": message, "user_id": user_id}).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}/agent/chat",
        data=payload,
        headers={"Content-Type": "application/json", "X-Request-ID": request_id},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit CLI endpoint.
            body = json.loads(response.read().decode("utf-8"))
            status = response.status
    except HTTPError as exc:
        status = exc.code
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except json.JSONDecodeError:
            body = {}
    except (TimeoutError, URLError):
        status = 0
        body = {}
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    trace = body.get("trace") if isinstance(body, dict) else {}
    trace = trace if isinstance(trace, dict) else {}
    return {
        "request_id_match": isinstance(body, dict) and body.get("request_id") == request_id,
        "http_status": status,
        "request_latency_ms": elapsed_ms,
        "generation_mode": trace.get("generation_mode"),
        "llm_call_count": trace.get("llm_call_count"),
        "failure_code": trace.get("failure_code"),
        "outcome": trace.get("final_outcome"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("AIRGUARD_API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--user-id", default=os.getenv("AIRGUARD_EVAL_USER_ID", DEFAULT_USER_ID))
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-p95-ms", type=float, default=DEFAULT_MAX_P95_MS)
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/release/stage2-load-probe.json"))
    args = parser.parse_args()
    if args.workers < 1 or args.rounds < 1 or args.workers > 4 or args.rounds > 4:
        parser.error("workers and rounds must be between 1 and 4")

    jobs = [MESSAGES[index % len(MESSAGES)] for index in range(args.workers * args.rounds)]
    results: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_one, args.base_url, args.user_id, message, args.timeout) for message in jobs]
        for future in as_completed(futures):
            results.append(future.result())
    latencies = [float(item["request_latency_ms"]) for item in results]
    deterministic = [item for item in results if item["generation_mode"] == "deterministic_grounded"]
    unexpected_llm = [item for item in results if item["llm_call_count"] != 0]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "base_url": args.base_url.rstrip("/"),
        "workers": args.workers,
        "rounds": args.rounds,
        "total_requests": len(results),
        "deterministic_grounded_requests": len(deterministic),
        "unexpected_llm_call_requests": len(unexpected_llm),
        "http_errors": sum(1 for item in results if int(item["http_status"]) != 200),
        "latency_ms": {
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
            "max": max(latencies) if latencies else None,
        },
        "results": results,
        "max_p95_ms": args.max_p95_ms,
        "result": "PASS"
        if results
        and len(deterministic) == len(results)
        and not unexpected_llm
        and all(item["http_status"] == 200 for item in results)
        and (percentile(latencies, 0.95) or float("inf")) < args.max_p95_ms
        else "BLOCKED",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['result']}: {args.output}")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
