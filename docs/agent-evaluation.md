# Agent Evaluation

## AI-002 fixture gate

Focused tests live in `tests/test_agents/test_grounding.py` and use
`FakeBackendToolClient`, so they require neither a database nor an LLM provider.

The AI-002 release gate covers:

- intent and expected tool arguments for current, impact assessment, history, compare, weather, forecast, alert and profile;
- spatial POI comparison and wind-vector questions must call `get_spatial_air_quality`, preserve model/weather provenance and label geometric inference;
- mandatory tool use even when a user says not to call tools;
- source mapping for environmental facts from the same request;
- AQI-first current-station responses that enumerate PM2.5, CO₂, noise and temperature from the same fresh snapshot;
- transparent handling of backend outage, empty history, stale, offline, invalid and invalid arguments;
- clarification for missing station context;
- refusal of prompt injection, medical diagnosis, emergency claims, device control and HITL bypass;
- trace request id, tool status/latency, final outcome and PII/secret redaction.

## AI-006 golden-set gate

The executable golden set is `eval/golden_cases/airguard_agent_v1.jsonl`. It contains 41 cases for
current, history, compare, weather, forecast, alert, profile, recommendation, proposal/no-proposal,
spatial comparison/wind analysis, no-data, stale/offline/invalid data, backend/tool failure, injection, and medical/device/HITL
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

For the AgentRouter/Claude gate used in Backlog 4, configure `AGENTROUTER_API_KEY` and
`AGENTROUTER_MODEL`, then run:

```powershell
.\.venv\Scripts\python.exe eval\run_live_evaluation.py --expected-provider agentrouter --max-p95-ms 2500
```

For Gemini 3.6 Flash, configure `GEMINI_API_KEY` and run:

```powershell
.\.venv\Scripts\python.exe eval\run_live_evaluation.py --expected-provider gemini --max-p95-ms 2500 --case-delay 1
```

Gemini áp quota theo Google Cloud project, không theo từng API key. Kết quả
`provider_daily_quota_exhausted` nghĩa là quota ngày của project/model đã hết; không rerun bộ
release cho đến khi quota reset hoặc project được nâng tier. Rate limit ngắn hạn sẽ tuân theo
`RetryInfo` của Google với exponential backoff có giới hạn.

The runner calls the canonical backend endpoint (`POST /api/v1/agent/chat`) for LIVE-01 through
LIVE-05 and writes a sanitized JSON and Markdown pack under
`docs/evidence/release/<date>-<git-sha>/`. It records input, expected and actual tools, source/tool
references, provider/model, LLM and request latency, output, request ID and PASS/FAIL. A case only
passes with `generation_mode=live_llm`; missing keys, an unavailable stack, deterministic fallback,
or any contract mismatch produces `BLOCKED` and a non-zero exit code rather than fabricated evidence.
The release gate also requires nearest-rank provider-latency P95 below 2.5 seconds and checks
station/source/simulator transparency terms for the three environmental-answer cases.

The Agent enforces `LLM_RESPONSE_DEADLINE_SECONDS` as a total generation deadline independent of
the provider HTTP retry policy. The default five-second deadline is shorter than the backend
proxy's eight-second timeout, so a slow provider produces a traced deterministic fallback instead
of an HTTP 503. Such fallback still fails the live release gate and is excluded from live P95.
