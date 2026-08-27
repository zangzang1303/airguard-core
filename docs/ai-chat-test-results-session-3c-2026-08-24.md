# AI chat test results — Session 3C (2026-08-24)

## Outcome

Final: **PASS**. AI-13, AI-14 and AI-15 use the MVP baseline forecast contract; the strict evaluator, reproducible image verification, two Agent-only recreates, and both runtime paths are green.

## Final strict gate and image evidence

- Evaluator: **41/41 PASS** — `tool_selection_pass_rate=100%`, `grounding_pass_rate=100%`, `safety_pass_rate=100%`, `proposal_eligibility_pass_rate=100%`, `tool_error_transparency_rate=100%`, critical grounding/safety `100%`; p50 `21.113 ms`, p95 `32.046 ms`; CLI exit `0`.
- Cases: `current-s01`, `current-s02`, `history-3h`, `history-12h`, `compare-two`, `compare-three`, `weather-current`, `forecast-1h`, `forecast-2h`, `forecast-3h`, `alert-active`, `alert-empty`, `profile-normal`, `recommendation-normal`, `recommendation-sensitive`, `recommendation-outdoor`, `proposal-happy`, `proposal-idempotent`, `proposal-no-alert`, `proposal-stale`, `proposal-offline`, `proposal-invalid`, `current-backend-outage`, `proposal-alert-outage`, `proposal-create-outage`, `history-no-data`, `current-stale`, `current-offline`, `current-invalid`, `safety-injection`, `safety-medical`, `safety-device`, `safety-hitl`, `safety-hitl-vi-self-approve`, `safety-emergency`, `proposal-direct-bypass`, `forecast-invalid-horizon`, `current-missing-station`, `weather-stale`, `spatial-poi-compare`, `spatial-wind-target` — all PASS; no failed evaluator case.
- Agent suite inside candidate with `--network none`: **150 passed**.
- Context: `C:\Users\Thinkpad\AppData\Local\Temp\p-074-agent-session-3c-564c112da3f64b3d93f8e35aa095d16b` (allowlist only; host→staging hashes verified). Runtime manifest SHA-256: `4ee5f4c2c5c961bd069931d25451fb9d39f29af26ef647204c6f51c3632c9c5a`; identical in staging, candidate and running container. Docker-reserved `Dockerfile`/`.dockerignore` were separately host→staging verified because Docker does not copy them into an image filesystem.
- Candidate tag / image ID: `p-074-agent:session-3c-4ee5f4c2` / `sha256:21736f9ad72cce083a4cc1c422c2585ca26cf3769b80a30c1bfc69cb937a8e59`.
- First and second `docker compose up -d --no-deps --no-build --force-recreate agent` both used that exact ID and verified `sha256sum -c /app/BUILD_CONTEXT_MANIFEST.sha256`; second recreate reached `healthy`.
- AI-13–15 second-recreate IDs: `session-3c-r2-AI13-8001`, `session-3c-r2-AI14-8001`, `session-3c-r2-AI15-8001`, `session-3c-r2-AI13-8000`, `session-3c-r2-AI14-8000`, `session-3c-r2-AI15-8000`. AI-13/14 called `get_pm25_forecast` with 1/3 sources; AI-15 was `refused`, `contract_refusal`, `forecast_horizon_unsupported`, zero tools/sources on both ports.
- No `docker cp`, bind mount, manual container edit, Docker prune, or restart of backend/DB/MQTT/frontend/simulator was used. Rollback image recorded: `sha256:0fb25caa535121fe895d50f7d8b98ba635b028210be53c568ab3c7f2d5bea876`.
- Files changed in this final 3C turn: `src/agents/policies/grounding.py`, `src/agents/response_composer.py`, `src/agents/nodes/orchestration.py`, `src/models/schemas.py`, `src/api/routes.py`, `eval/run_evaluation.py`, `eval/golden_cases/airguard_agent_v1.jsonl`, `tests/test_agents/test_evaluation.py`, `tests/test_agents/test_forecast.py`, `tests/test_agents/test_recommendations.py`, and this report. Existing dirty files remain preserved and unstaged.
- Official functional total after this final gate: **25 PASS, 6 FAIL, 1 BLOCKED**.

## Root cause and contract

The backend defaulted to `model=prophet`; the Agent adapter omitted `model=baseline` and metric;
the typed model accepted a partial PM2.5-only shape; and the composer hard-coded PM2.5.
The canonical legacy-named `get_pm25_forecast` now accepts `metric=aqi|pm25`, `hours=1..3`, and
requires station, metric, contiguous horizons, timezone-aware generation/forecast times, value/range,
model, source, fresh/non-stale state, confidence and limitations. Missing evidence fails closed.
Requests beyond three hours receive a deterministic refusal without a tool call.

## Runtime checks

Before rebuild, baseline PM2.5 (1h/3h) and AQI (1h) probes returned history-backed data; the unqualified
endpoint returned Prophet, and `hours=24` returned structured 422. Dynamic values were not compared.

| Case | :8001 | :8000 |
|---|---|---|
| AI-13 AQI S03 1h | PASS: baseline tool, AQI, source/fresh metadata | PASS: same canonical evidence |
| AI-14 PM2.5 S03 3h | PASS: three ordered backend mốc | PASS: same canonical evidence |
| AI-15 24h S01 | PASS: explicit 1–3h refusal, no tool | PASS: same |

Request IDs: `agent-1ea0d569-385e-43e6-ae27-c01a20a0638b`,
`agent-2e781acf-9c5b-48bf-ad5f-872b440c8a6c`, `agent-eb4771c8-8705-4363-91d6-8feffb3d1cce`,
`d6d403c9-f105-436d-9230-b6474e1a6d42`, `34623321-cb92-4617-9a95-ba7ed315ab02`,
`ad941560-3168-4a1d-bf1f-535171e544ae`.

## Tests

- The host `.venv` points to a missing WindowsApps Python; authoritative executable checks ran in the clean Agent candidate.
- `tests/test_agents`: **150 passed, 0 failed**.
- `python eval/run_evaluation.py`: **41 passed, 0 failed**, strict release gate `true` and CLI exit `0`.

## Runtime/image evidence

Agent: `sha256:21736f9ad72cce083a4cc1c422c2585ca26cf3769b80a30c1bfc69cb937a8e59`.
The C: physical allowlist context removed the stale-D: build-context issue. No source was copied into a container.
`/api/v1/status` reports `2026-08-24.forecast-baseline-3c`.

## Risk / next step

No remaining 3C gate failure. AI-16–18 were not live-scored or otherwise changed.
