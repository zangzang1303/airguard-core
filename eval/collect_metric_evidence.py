"""Generate a dated, non-destructive evidence pack for the Agent quality gate.

The canonical ``run_evaluation.py`` runner historically writes to a fixed filename.
This companion runner executes the same golden cases but writes a caller-selected
JSON file, so an assessment never overwrites a previous release artifact.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.run_evaluation import DEFAULT_CASES, _metrics, _run_case, load_cases  # noqa: E402


def _rate(values: list[bool]) -> float | None:
    return round(100 * sum(values) / len(values), 2) if values else None


async def collect(cases_path: Path) -> dict[str, Any]:
    cases = load_cases(cases_path)
    results = [await _run_case(case) for case in cases]
    category_counts = Counter(case["category"] for case in cases)
    category_passes = Counter(
        result.category for result in results if result.passed
    )
    critical = [result for result in results if result.critical]
    return {
        "schema_version": "airguard-metric-evidence-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "measurement": {
            "name": "deterministic_agent_golden_set",
            "method": "Executes the repository golden set with FakeBackendToolClient; no live database, MQTT broker, browser, user telemetry, or LLM provider is used.",
            "scope": "Regression evidence for Agent routing, grounding, safety, proposal eligibility, and transparent failure handling.",
            "golden_set": cases_path.relative_to(ROOT).as_posix(),
        },
        "metrics": _metrics(results),
        "breakdowns": {
            "by_category": [
                {
                    "category": category,
                    "case_count": category_counts[category],
                    "passed_cases": category_passes[category],
                    "pass_rate": _rate(
                        [result.passed for result in results if result.category == category]
                    ),
                }
                for category in sorted(category_counts)
            ],
            "critical_cases": {
                "case_count": len(critical),
                "passed_cases": sum(result.passed for result in critical),
                "pass_rate": _rate([result.passed for result in critical]),
            },
        },
        "known_measurement_gaps": [
            "This result is deterministic fixture evidence, not live-provider quality evidence.",
            "No running-stack measurement is included for MQTT ingestion, API availability, alert latency, or device acknowledgement.",
            "No product telemetry is available for activation, task completion, retention, satisfaction, or trusted-decision sessions.",
            "Simulator data cannot establish real-world sensor accuracy, clinical safety, or environmental impact.",
        ],
        "cases": [{**asdict(result), "passed": result.passed} for result in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = asyncio.run(collect(args.cases.resolve()))
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
