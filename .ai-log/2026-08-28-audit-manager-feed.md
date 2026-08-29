# AI Work Log

## Date / agent / machine

2026-08-28 / Codex / local Windows workspace

## Goal

Make the manager-facing Audit Log easier to read, include a station area for new automatic-proposal records, and prevent routine/logout and pending automation activity from cluttering the management feed.

## Context read

`AGENTS.md`, current Audit Log frontend and API mapper, automatic proposal service and its backend tests.

## Files changed

- `frontend/src/features/audit/AuditLog.tsx`
- `frontend/src/features/audit/AuditLog.css`
- `frontend/src/api/client.ts`
- `frontend/src/types/index.ts`
- `backend/app/services/automatic_proposal_service.py`
- `tests/test_backend/test_automatic_proposal_service.py`
- `backend/app/services/approval_service.py`
- `tests/test_backend/test_quick_approval.py`

## Decisions and rationale

- The backend audit ledger remains append-only: proposal creation and review records are retained for safety and traceability.
- The manager UI is now an approval history: it displays only `approval.approve` / quick-approve events. Alerts, authentication, pending/rejected/expired proposals, and automation events are hidden.
- Approval audit details now retain the proposal's `station_id` and proposed action. For older immutable audit rows that lack this metadata, the UI joins the approval request by ID before rendering the station area.
- Automatic-proposal audit metadata now records `station_id`; the UI renders the corresponding station name as the area when available.
- The existing auto-proposal trigger was already 30 seconds. Notification delivery is still disabled because no Resend configuration is active.

## Commands/tests run and results

- `./.venv/Scripts/python.exe -m pytest tests/test_backend/test_automatic_proposal_service.py` — 8 passed.
- `docker compose exec -T frontend npm run build` — passed (rerun after approval-history-only filter).
- `./.venv/Scripts/python.exe -m pytest tests/test_backend/test_quick_approval.py` — 8 passed.
- `docker compose exec -T frontend npm run build` and backend rebuild — passed after station-area display update.
- Rebuilt backend with Docker Compose and verified `/health` returned `status: ok` during this session.
- `git diff --check` — no whitespace errors; Git reported only CRLF normalization warnings.

## Contracts/risks changed

No public API contract changed. `station_id` is an additive field in backend audit details. Existing historical audit rows without it cannot show a station area.

For a user-requested runtime test, the simulator was temporarily switched to `spike` and the local trigger to 5 seconds. A pending S03 `ventilation_boost` request was created and approved during the test. The simulator is back to `normal`; the user subsequently set the local trigger to 15 minutes (900 seconds).

## Blockers/open questions

To test a real manager email notification, configure a valid Resend provider/key/sender in the local `.env`; the current provider is disabled.

## Next exact step

Confirm the approved S03 request appears in the approval-only Audit Log, then continue normal simulator operation.

## Handoff IDs (request/message/proposal/job)

No durable external IDs captured.
