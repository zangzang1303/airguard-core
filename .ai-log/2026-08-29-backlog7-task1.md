# AI Work Log

## Date / agent / machine

- 2026-08-29 / Codex / Windows workspace `P-074`

## Goal

- Hoàn thiện và xác minh B7-01: forecast 1–24h, golden windows, Agent grounding và timeline simulation.

## Context read

- `AGENTS.md`
- `tasks/backlog7/task1-forecast-prophet-timeline.md`
- `specs/api-contracts.md`
- `docs/agent-evaluation.md`
- `templates/ai-log-template.md`

## Files changed

- Backend forecast service, station history adapter, API routes and forecast tests.
- Agent forecast contracts, routing, backend/fake adapters, composer and evaluation cases.
- Frontend timeline dock, slider, API/types/styles and regression contract.
- ADR 0019, benchmark runner/evidence, README, API spec and task status.

## Decisions and rationale

- Keep the legacy `ProphetForecastService` import name, but label the implementation and API provenance as `extended_additive_fourier_v3`; the third-party Prophet library is not installed.
- Preserve the baseline model for 1–3h and require `model=extended` for longer horizons through 24h.
- Golden windows require at least two contiguous hours with AQI at most 50 and projected wind at least 2 m/s; the rule is not relaxed when no window exists.
- Longer-horizon forecasts remain simulator-grounded and cannot drive alerts or device actions.

## Commands/tests run and results

- `python eval/run_prophet_benchmark.py`: PASS; latest post-merge run PM2.5 MAE 5.65 -> 1.84, improvement 67.5%.
- Targeted backend/Agent pytest suite: original 149-test gate passed; post-merge expanded rerun passed 187 tests with 1 dependency deprecation warning.
- Task-specific frontend timeline contract: 4 passed.
- `npm.cmd --prefix frontend run build`: PASS; TypeScript and Vite production build completed.
- Ruff on Task 1 implementation/tests excluding pre-existing unused imports in `backend/app/main.py`: PASS.
- `docker compose config --quiet`: PASS.
- `docker compose up --build -d`: PASS; PostgreSQL/backend healthy, Agent/frontend/MQTT/consumer/simulators running.
- Docker live API smoke-check: PASS for S01-S05; 24 ordered points per station, widening bounds, non-increasing confidence, baseline 24h guard 422, 468 spatial grid points at +24h.
- Agent live: PASS; `get_pm25_forecast` with AQI/S01/24h, grounded simulator sources, deterministic fallback when provider exceeded deadline.
- Edge headless live E2E: PASS; Pause held +2h, two 0→24h cycles completed in 19,563ms and 19,611ms, golden card/chart visible, all 33 forecast/spatial responses returned 200, no JavaScript page errors, heap delta -4,718,463 bytes.
- Post-merge wiring repair (2026-08-30): restored the extended forecast service import, timeline dock/type imports and refresh revision prop after branch integration; 187 backend/Agent tests, 4 timeline contract tests, Ruff and frontend production build passed.
- Post-merge Docker/API/UI verification (2026-08-30): all services healthy; S01-S05 returned 24 ordered bounded extended-AQI points, baseline 24h guard returned 422, spatial +24h returned 468 grid points from all 5 stations; Edge headless confirmed Manager login, S01 timeline/golden card/chart, Pause held +2h, auto-stop at +24h, 6/6 Task 1 responses successful and no page errors.

## Contracts/risks changed

- Forecast API and Agent typed contract now support 1–24h with explicit baseline/extended selection.
- Added golden-window response contract and additive forecast provenance.
- Browser-level playback, interval cleanup and memory behavior were verified on the running Docker stack.

## Blockers/open questions

- No implementation blocker remains for the accepted lightweight additive-Fourier scope.
- If the mentor requires the third-party Meta Prophet package literally, that is a separate dependency/architecture decision; the current implementation deliberately does not claim to be Prophet.

## Next exact step

- Review the Task 1 diff and commit it as one contract-first change; keep the live stack available for demo or stop it explicitly when no longer needed.

## Handoff IDs (request/message/proposal/job)

- None.
