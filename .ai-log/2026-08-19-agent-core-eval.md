# AI Work Log

## Date / agent / machine

2026-08-19 / Codex / Windows workspace `E:\Vinproject\P-074`

## Goal

Complete `tasks/backlog4/agent-core-eval.md`: grounded hybrid Agent flow, three-group
recommendation policy, safety refusals, AgentRouter/Claude live boundary, and executable release gates.

## Context read

`AGENTS.md`, `README.md`, `tasks/ai-agent.md`, `tasks/backlog3/agent-live-llm.md`,
`tasks/backlog4/agent-core-eval.md`, `docs/agent-evaluation.md`, ADR 0004, Agent source/tests/eval harness.

## Files changed

- Agent/provider: `src/config.py`, `src/services/llm.py`, `src/agents/graph.py`,
  `src/agents/nodes/orchestration.py`, grounding/recommendation/composer policies.
- Gates/tests: Agent tests, live-eval tests, golden cases, live runner and generated sanitized evidence.
- Runtime/docs: `.env.example`, `docker-compose.yml`, Claude launcher, README, ADR 0004,
  evaluation docs, backlog status.
- Local-volume compatibility: `backend/db/schema.sql` adds the missing idempotent temperature migration.

## Decisions and rationale

- `LLM_PROVIDER=auto` prefers AgentRouter/Claude only when key and model are both configured;
  OpenAI remains compatible. Provider failure keeps the deterministic grounded answer and never
  claims `live_llm`.
- Claude uses Anthropic Messages over a small typed HTTP boundary with timeout, one bounded retry,
  usage mapping and sanitized failure codes.
- Recommendation policy v2 always obtains five-station comparison evidence. Outdoor users receive
  the best current AQI station plus the lowest point in the requested station forecast; sensitive
  users receive early indoor-protection advice outside the good band.
- Live P95 is calculated only from successful `live_llm` calls. Authentication-failure latency is
  not accepted as model latency.

## Commands/tests run and results

- `pytest tests/test_agents tests/test_scripts/test_live_evaluation.py -q`: 102 passed.
- `pytest tests -q`: 164 passed, one third-party Starlette deprecation warning.
- Focused Ruff on all changed Python files: pass.
- `eval/run_evaluation.py`: 39/39; grounding, safety, tool selection, proposal eligibility and
  tool-error transparency 100%; deterministic P95 221.236 ms.
- Docker build/health/current/forecast gates: pass after non-destructive local-volume migration.
- Live eval with `--expected-provider agentrouter --max-p95-ms 2500`: BLOCKED; LIVE-01..05 all
  safely fell back with `failure_code=provider_authentication_failed`; no valid live P95.

## Contracts/risks changed

- New typed envs: `LLM_PROVIDER`, `LLM_MAX_RETRIES`, `AGENTROUTER_API_KEY`,
  `AGENTROUTER_MODEL`, `AGENTROUTER_BASE_URL`.
- Recommendation tool trace now includes `compare_stations` for all personalized recommendation requests.
- Live evidence requires provider match, transparency terms and P95 below 2.5 seconds.

## Blockers/open questions

AgentRouter rejects the configured key on Anthropic Messages and OpenAI-compatible probes with HTTP
401 `unauthorized client detected`. Key rotation/account support is external to the repository.

## Next exact step

Sau khi quota Gemini của project reset hoặc project được nâng tier, chạy:

```powershell
docker compose up -d --force-recreate agent
.\.venv\Scripts\python.exe eval\run_live_evaluation.py --expected-provider gemini --max-p95-ms 2500 --case-delay 15
```

Only mark the three live checklist items complete if all five cases are `PASS` and live P95 is below target.

## Handoff IDs (request/message/proposal/job)

Sanitized evidence pack: `docs/evidence/release/2026-08-19-de4b2e817b88/`.
Per-case request IDs are stored in its `live-eval.json`; no proposal or device mutation occurred.

## Gemini migration addendum

- Switched `auto` provider priority to Gemini and added the official Generate Content REST boundary
  for stable model `gemini-3.5-flash`.
- Gemini uses `thinkingLevel=MINIMAL`, 32 output tokens, no sampling override, and a process-scoped
  HTTP client. The model prompt contains only locked outcome plus evidence-present/none; it never
  receives measurement values, station identifiers or the deterministic answer.
- Full regression after migration: 168 passed; focused Ruff pass.
- Direct provider smoke: success with usage metadata. Container confirmed provider/model/key status.
- One live run reached 5/5 functional PASS but missed latency P95 (5.08 s). After optimization a
  successful live call measured 1.49 s, but repeated release runs were blocked by intermittent HTTP
  429 from the configured Gemini project. Current formal evidence remains BLOCKED until quota permits
  five successful cases in one run.
- Retry command after quota reset:

```powershell
.\.venv\Scripts\python.exe eval\run_live_evaluation.py --expected-provider gemini --max-p95-ms 2500 --case-delay 15
```

## HTTP 429 root-cause addendum

- Sanitized Google `QuotaFailure` identified
  `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, value 20, for `gemini-3.5-flash`.
- This is a per-project/model daily limit, not an invalid key. Rotating a key in the same project
  does not restore quota.
- Gemini now fails fast with `provider_daily_quota_exhausted` and does not retry daily quota.
  Short-term rate limits honor `RetryInfo`; other transient failures use bounded exponential
  backoff.
- Verification: full suite `170 passed`, focused Ruff and `git diff --check` passed. Rebuilt the
  Agent container; an in-container runtime request returned HTTP 200 with grounded deterministic
  fallback, `provider_daily_quota_exhausted`, 401.71 ms provider latency and one tool call.

## Gemini 3.6 migration

- User requested migration to stable model ID `gemini-3.6-flash` before rerunning the final live
  criteria. Defaults, Compose, documentation and provider contract tests were updated together.
- Verification: `170 passed`, Ruff and Compose config passed; rebuilt container reports
  `model=gemini-3.6-flash` with configured key. Initial smoke returned `live_llm` in 3043.827 ms.
- Formal five-case rerun through `http://127.0.0.1:8000/api/v1` was `BLOCKED`: all cases received
  backend HTTP 503 at its 8-second Agent timeout. A cooled direct Agent call still returned
  `live_llm` in 10549.368 ms, so the 2500 ms P95 gate cannot honestly be marked pass.
- Priority entitlement probe sent `serviceTier=priority`, but the response header reported
  `x-gemini-service-tier=standard` and HTTP 429 identified
  `GenerateRequestsPerDayPerProjectPerModel-FreeTier` with value 20. Priority is not enabled in
  code because this project remains free tier; enabling it requires a billing/tier change outside
  the repository and carries a documented 75-100% price premium.

## Verification addendum - 2026-08-20

- Rebuilt and started the full Compose stack; backend and Agent health checks passed, and MQTT
  measurements for S01-S05 were accepted after multiple simulator cycles.
- Task-specific gates: Task 1 `70 passed`, Task 2 `12 passed`, Task 3 `39 passed`.
- Full offline gate: `170 passed` with one third-party Starlette deprecation warning.
- Golden evaluation: `39/39`; tool selection, grounding, safety, proposal eligibility and tool-error
  transparency all 100%; deterministic P95 49.432 ms.
- Focused Ruff for Agent/eval files and `git diff --check`: pass. Whole-repo Ruff still reports 20
  pre-existing issues in backend/IoT files outside this task's scope.
- The formal Gemini rerun was not sent: execution approval rejected the external egress until the
  user explicitly authorizes Gemini. The provider prompt contains only locked outcome and
  evidence-present/none, not measurements, station IDs, profiles or the deterministic answer.

## Authorized live rerun and timeout remediation - 2026-08-20

- User explicitly authorized the five minimal provider prompts. Formal evidence was written to
  `docs/evidence/release/2026-08-20-de4b2e817b88-gemini/`.
- Result: `BLOCKED`, `2/5 PASS`, provider P95 `7411.95 ms`. LIVE-02 was live in 1134.867 ms and
  LIVE-04 in 7411.95 ms. LIVE-01/LIVE-03 hit the backend's eight-second proxy timeout; LIVE-05
  safely fell back with `provider_daily_quota_exhausted`.
- Added `LLM_RESPONSE_DEADLINE_SECONDS=5` as a total orchestration deadline. It is shorter than the
  backend proxy timeout, cancels slow provider work, preserves the grounded deterministic answer,
  records `provider_deadline_exceeded`, and never claims `live_llm`.
- Added deadline regression coverage and updated env/Compose/README/evaluation/ADR contracts.
  Verification after the fix: `171 passed`, golden `39/39` with all critical metrics 100%, focused
  Ruff pass, `git diff --check` pass, rebuilt Agent/backend healthy, container deadline confirmed 5s.
- Do not rerun the formal set until Gemini daily quota resets or the project gains sufficient paid
  capacity. The live checklist remains open until one five-case run is fully live with P95 < 2.5s.
