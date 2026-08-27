# AI Work Log

## Date / agent / machine

2026-08-10 / Codex / local Windows workspace.

## Goal

Make the local AirGuard MVP runnable end-to-end and remove known demo integration blockers.

## Context read

`AGENTS.md`, Compose topology, backend/data contracts, runtime logs, frontend API client,
LangGraph workflow, database schema and demo runbooks.

## Files changed

- Split database structure and demo data into `backend/db/schema.sql` and `backend/db/seed.sql`.
- Added `scripts/init-demo-db.ps1` for an idempotent bootstrap of an existing local database volume.
- Corrected `.env.example` header corruption and added the seed mount to Compose.
- Mapped core frontend station/history/forecast/alert/approval/audit requests to backend contracts and removed their runtime fallback behavior.
- Wired the LangGraph proposal intent to `run_proposal_workflow`, exposed `proposal_id`, and added graph coverage.
- Added backend MQTT host/port for approved device commands and dispatch outcome/audit persistence.
- Updated setup/demo/completion documentation.

## Decisions and rationale

- Keep `schema.sql` and `seed.sql` idempotent for MVP setup; use migrations such as Alembic in a later shared/production phase.
- The core dashboard must fail visibly when canonical API data is unavailable rather than display invented environmental values.
- Agent proposal creation remains pending-manager-only; it cannot approve/reject or publish MQTT directly.

## Commands/tests run and results

- `python -m compileall -q backend/app src services/mqtt-consumer services/sensor-simulator services/device-simulator`: passed after fixing a task indentation error.
- `python tests/test_backend/test_services.py`: 10 pass.
- `python tests/test_backend/test_api_contract.py`: 4 pass; one Starlette/httpx deprecation warning.
- `npm.cmd --prefix frontend run build`: passed.
- `git diff --check`: passed.
- LangGraph pytest/smoke was not run locally because the active host Python lacks `langgraph`; the Docker Agent image installs root `requirements.txt`.

## Contracts/risks changed

- New demo seed includes S01-S05, FILTER-01 and dashboard demo user profiles.
- Frontend core approval/audit calls now require manager headers and a proposal `version`; admin P2 placeholder surfaces remain outside the backend RBAC contract.
- Runtime verification is still mandatory for MQTT-to-DB and approved-device command acknowledgement.

## Blockers/open questions

- Docker Engine is unavailable from the current execution context: `dockerDesktopLinuxEngine` named pipe is missing.
- Existing local Postgres volume must receive `schema.sql` and `seed.sql` through `scripts/init-demo-db.ps1` before the consumer can persist measurements.
- Agent runtime requires dependencies available through Compose or `python -m pip install -r requirements.txt` in the active virtual environment.

## Next exact step

Start Docker Desktop, then run:

```powershell
.\scripts\init-demo-db.ps1
docker compose up -d --build
docker compose logs --tail=100 mqtt-consumer
```

Verify a fresh row exists in `measurements`; then run the spike, Agent proposal, manager approval and device-status scenarios in `docs/demo-runbook.md`.

## Handoff IDs (request/message/proposal/job)

No runtime proposal/job ID yet.
