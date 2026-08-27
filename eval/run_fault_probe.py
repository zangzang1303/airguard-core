"""Hermetic semantic-router fault matrix; production answers remain deterministic."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.agents.policies.semantic_router as semantic_router
from src.services.llm import LlmProviderError


class _Reply:
    content = '{"intent":"current","station_ids":["S01"],"hours":null,"metric":null,"comparison_mode":null,"confidence":0.99,"needs_clarification":false}'
    usage_metadata = {}


class _Provider:
    def __init__(self, failure: Exception | None = None) -> None:
        self.failure = failure

    async def ainvoke(self, _prompt: str) -> _Reply:
        if self.failure is not None:
            raise self.failure
        return _Reply()


async def _run_case(name: str, failure: Exception | None) -> dict[str, object]:
    original_get_llm = semantic_router.get_llm
    original_provider = semantic_router.resolve_llm_provider
    semantic_router.get_llm = lambda **_kwargs: _Provider(failure)
    semantic_router.resolve_llm_provider = lambda _settings: "openai"
    settings = SimpleNamespace(
        semantic_router_enabled=True,
        semantic_router_confidence_threshold=0.8,
        semantic_router_deadline_seconds=0.01,
        llm_provider="openai",
        openai_api_key="fault-probe-key",
        model_name="gpt-4o",
    )
    try:
        telemetry: dict[str, object] = {}
        result = await semantic_router.classify_semantically(
            "S01 có đáng lo không?", settings=settings, telemetry=telemetry
        )
        return {
            "case": name,
            "logical_invocations": telemetry.get("llm_call_count"),
            "failure_code": telemetry.get("failure_code"),
            "semantic_router_outcome": telemetry.get("semantic_router_outcome"),
            "safe": result is None if failure else result is not None,
        }
    finally:
        semantic_router.get_llm = original_get_llm
        semantic_router.resolve_llm_provider = original_provider


async def _run() -> list[dict[str, object]]:
    return [
        await _run_case("timeout", TimeoutError("simulated timeout")),
        await _run_case("provider_429", LlmProviderError("provider_rate_limited")),
        await _run_case("provider_5xx", LlmProviderError("provider_http_503")),
        await _run_case("malformed", LlmProviderError("provider_malformed_response")),
        await _run_case("success", None),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/release/stage2-fault-matrix.json"))
    args = parser.parse_args()
    cases = asyncio.run(_run())
    report = {
        "cases": cases,
        "result": "PASS" if all(case["safe"] for case in cases) else "BLOCKED",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['result']}: {args.output}")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
