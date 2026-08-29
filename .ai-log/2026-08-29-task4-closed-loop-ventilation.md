# AI Work Log

## Date / agent / machine

2026-08-29 / Codex / Windows workspace `E:\Vinproject\P-074`

## Goal

Implement Task 4: Manager-only ventilation map, closed-loop simulator feedback, grounded Agent device status, strict HITL and audit preservation.

## Context read

`AGENTS.md`, `README.md`, `tasks/backlog7/task4-auto-ventilation-hitl-audit.md`, API/data/domain specs, existing ventilation/approval/device/Agent/frontend code and related tests.

## Files changed

Backend device/runtime API and policy services; sensor/device simulators and MQTT schema; Agent tool/router/composer; React map marker/drawer/heatmap refresh; contracts, ADR 0019, tests and Task 4 status.

## Decisions and rationale

- Restore the Task 4 continuity default to 15 minutes.
- Separate recovery thresholds from trigger thresholds: PM2.5 < 25 µg/m³ and CO₂ < 700 ppm for 20 continuous minutes.
- Apply feedback only after a correlated successful ACK and stop it at cycle expiry.
- Keep Eco and Standby UI actions as pending proposals; the browser never publishes a device command.
- Report measured increases as increases, never as reductions.

## Commands/tests run and results

- `ruff check` on Task 4 Python files: passed.
- `compileall`: passed.
- `pytest tests/test_backend tests/test_agents tests/test_iot -q`: 584 passed, one third-party deprecation warning.
- Task-focused tests: 176 passed; map/heatmap contract subset: 9 passed.
- `npm run build`: passed.
- `npm run test:ai-resilience`: 19 passed, including live backend pass-through.
- `docker compose config --quiet`: passed with local Docker config warning.
- `docker compose up --build -d`: passed; backend and Agent health endpoints returned OK.
- Live ventilation endpoint returned simulator runtime data; live Agent selected `get_ventilation_devices_status` and returned a grounded answer.
- Full frontend contract suite: 87 passed, 11 pre-existing out-of-scope regressions remain in navigation/search/default legend contracts.

## Contracts/risks changed

Added rich ventilation status endpoint/tool and additive device ACK fields. Documented the exponential demo model and strict recovery thresholds. This remains simulated/non-certified and does not control physical devices.

## Blockers/open questions

No Task 4 blocker. Full browser automation of the 45-minute scenario was not run; deterministic unit/integration coverage and live read-path smoke checks were used. Eleven unrelated frontend contract regressions remain.

## Next exact step

Optionally run the documented live demo scenario with an authenticated Manager and observe the full proposal → approval → dispatch → ACK → recovery flow over accelerated demo timing.

## Handoff IDs (request/message/proposal/job)

Live smoke request IDs were transient and no new proposal was created, avoiding mutation of existing approval data.
