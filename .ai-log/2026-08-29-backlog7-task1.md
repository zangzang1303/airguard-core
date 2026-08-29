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

- `python eval/run_prophet_benchmark.py`: PASS; PM2.5 MAE 7.67 -> 1.87, improvement 75.6%.
- Targeted backend/Agent pytest suite: 149 passed, 1 dependency deprecation warning.
- Task-specific frontend timeline contract: 4 passed.
- `npm.cmd --prefix frontend run build`: PASS; TypeScript and Vite production build completed.
- Ruff on Task 1 implementation/tests excluding pre-existing unused imports in `backend/app/main.py`: PASS.
- `docker compose config --quiet`: PASS.
- `docker compose ps`: not runnable because the local Docker daemon is stopped.

## Contracts/risks changed

- Forecast API and Agent typed contract now support 1–24h with explicit baseline/extended selection.
- Added golden-window response contract and additive forecast provenance.
- Remaining risk is browser-level smoothness and memory observation on a running stack.

## Blockers/open questions

- Docker daemon is not running, so the manual live UI checklist has not been executed.

## Next exact step

- Start Docker Desktop, run `docker compose up --build -d`, open the heatmap, play/pause 0–24h, verify golden-window cards and observe browser memory during at least two complete playback cycles.

## Handoff IDs (request/message/proposal/job)

- None.
