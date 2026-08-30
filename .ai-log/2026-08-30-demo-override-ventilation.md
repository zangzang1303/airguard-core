# AI Work Log

## Date / agent / machine

2026-08-30 / Codex / local

## Goal

Make a demo station override enter the normal alert and manager-approval flow after the configured ventilation continuity duration.

## Context read

`AGENTS.md`, `backend/app/main.py`, demo telemetry, station, alert, ventilation and automatic-proposal services, frontend demo control, API contract and existing ventilation tests.

## Files changed

- `backend/app/main.py`
- `frontend/src/features/drawers/DemoStationControl.tsx`
- `specs/api-contracts.md`
- `tests/test_backend/test_demo_station_override.py`

## Decisions and rationale

Demo overrides remain in-memory overlays and do not fabricate MQTT/measurement history. The telemetry ticker now evaluates active overrides every 10 seconds through the same alert and automatic-proposal/HITL side effects as ingestion. A qualifying override can therefore create a pending request only; it cannot approve or dispatch a device command. The demo UI displays the configured continuity wait after apply.

## Commands/tests run and results

- `npm run build` in `frontend`: passed.
- Docker backend build: passed; backend container health check passed after recreation.
- Docker: `python -m pytest -q tests/test_backend/test_demo_station_override.py tests/test_backend/test_auto_ventilation.py`: 17 passed.
- `git diff --check`: passed (only existing CRLF warnings were emitted).

## Contracts/risks changed

The demo override PUT response now includes `ventilation_trigger`; the API contract documents 10-second ticker evaluation and the pending-only HITL result. Ticker timing means a proposal is created on the first ticker cycle at or after the configured duration (normally within one additional tick).

## Blockers/open questions

None.

## Next exact step

As Manager, apply an over-threshold PM2.5 or CO2 demo override, wait at least `VENTILATION_TRIGGER_SECONDS` plus one ticker interval, and inspect the Manager approval drawer for the pending request.

## Handoff IDs (request/message/proposal/job)

None created by this change.
