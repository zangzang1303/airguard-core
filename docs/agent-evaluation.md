# Agent Evaluation

## AI-002 fixture gate

Focused tests live in `tests/test_agents/test_grounding.py` and use
`FakeBackendToolClient`, so they require neither a database nor an LLM provider.

The AI-002 release gate covers:

- intent and expected tool arguments for current, impact assessment, history, compare, weather, forecast, alert and profile;
- mandatory tool use even when a user says not to call tools;
- source mapping for environmental facts from the same request;
- AQI-first current-station responses that enumerate PM2.5, CO₂, noise and temperature from the same fresh snapshot;
- transparent handling of backend outage, empty history, stale, offline, invalid and invalid arguments;
- rejection of missing freshness, timezone-less environmental timestamps, stale weather and stale forecast;
- simulator/fixture transparency for current, history, compare, weather, forecast and alert answers;
- clarification for missing station context;
- refusal of prompt injection, medical diagnosis, emergency claims, device control and HITL bypass;
- trace request id, tool status/latency, final outcome and PII/secret redaction.

## AI-006 golden-set gate

The executable golden set is `eval/golden_cases/airguard_agent_v1.jsonl`. It contains 39 cases for
current, history, compare, weather, forecast, alert, profile, recommendation, proposal/no-proposal,
no-data, stale/offline/invalid data, backend/tool failure, injection, and medical/device/HITL
refusal. Every case defines expected intent, tools, arguments, allowed facts, forbidden claims, and
proposal expectation.

Metrics: tool-selection pass, fact-to-tool grounding pass, safety pass, proposal eligibility pass,
tool-error transparency, p50/p95 latency. Critical target: 100% grounding and safety on demo cases.
Store request trace/fixture version; redact secrets/PII. Any ungrounded environmental fact blocks
demo until its regression test passes.

Run the deterministic evaluation without a database or LLM provider:

```powershell
.\.venv\Scripts\python.exe eval\run_evaluation.py
```

The runner writes Markdown and JSON reports to `eval/reports/`. The baseline rerun on 2026-08-11 has
39 cases and 100% tool selection, grounding, safety, proposal eligibility and tool-error
transparency. Recommendation graph integration is covered by the same deterministic fixture gate.

## Live LLM evidence (Gate 2)

The deterministic report above is a regression gate; it does not count as live-provider evidence.
With the Docker stack healthy, fresh simulator data available, and `OPENAI_API_KEY` configured only
in the local environment, run:

```powershell
.\.venv\Scripts\python.exe eval\run_live_evaluation.py
```

The runner calls the canonical backend endpoint (`POST /api/v1/agent/chat`) for LIVE-01 through
LIVE-05 and writes a sanitized JSON and Markdown pack under
`docs/evidence/release/<date>-<git-sha>/`. It records input, expected and actual tools, source/tool
references, provider/model, LLM and request latency, output, request ID and PASS/FAIL. A case only
passes with `generation_mode=live_llm`; missing keys, an unavailable stack, deterministic fallback,
or any contract mismatch produces `BLOCKED` and a non-zero exit code rather than fabricated evidence.
