# AI Work Log

## Date / agent / machine

2026-08-30 / Codex / local workspace

## Goal

Render the Agent's recommended running route clearly on the map with a lighter highlight and a dashed access segment from the user's current location to the graph snap point.

## Context read

`AGENTS.md`, `README.md`, `tasks/frontend.md`, `specs/api-contracts.md`, route-service and map-action implementation, plus running-route tests.

## Files changed

- `backend/app/services/geospatial_agent_service.py`
- `frontend/src/features/map/MapActionController.ts`
- `specs/api-contracts.md`
- `tests/test_backend/test_running_route_engine.py`

## Decisions and rationale

- Backend emits `approach_coordinates` from the submitted origin to the audited road-graph snap point, with `approach_kind=origin_to_graph_snap`.
- Frontend renders that connector as a blue dashed estimated-access line. It is explicitly separate from the evaluated running route and does not alter route distance or exposure.
- Recommended route styling now uses a lighter teal palette, thinner core/segment strokes, and a softer halo for map readability.

## Commands/tests run and results

- `./.venv/Scripts/python.exe -m pytest tests/test_backend/test_running_route_engine.py -q -k distance_and_detour_precision` — passed.
- `npm run build` in `frontend/` — passed.
- Full `test_running_route_engine.py` ran: 14 passed, 1 existing unrelated failure. The failing expectation requires a vague “tonight” route request to return `insufficient_data`, but the current code returns a forecast route.
- Runtime notification rehearsal: S03 `spike` created PM2.5/AQI alerts; with an ephemeral 60-second continuity window it created one pending proposal and enqueued two manager/admin notification jobs. Both completed `not_configured` because the provider remained disabled; no external email was sent. The simulator and backend were then recreated with default `normal`/900-second settings. The two spike-created alerts resolved.
- `./.venv/Scripts/python.exe -m pytest tests/test_backend/test_notification_tasks_resend.py tests/test_backend/test_person_b_api_security.py -q -k notification` — 7 passed.

## Contracts/risks changed

`highlight_route` now optionally carries `approach_coordinates`, `approach_kind`, and `approach_distance_m`; documented in the API contract. The connector is not turn-by-turn or graph-route geometry.

## Blockers/open questions

No blocker for this change. The full-file forecast assertion should be reviewed separately.

## Next exact step

Start the stack, set a location with GPS/map selection, ask for a running route, and visually verify the light teal route plus the dashed approach line.

## Handoff IDs (request/message/proposal/job)

None.

---

## Follow-up: shared Manager Activity Log

### Goal

Show every Manager/Admin account the same Activity Log, restricted to requests that a manager approved or rejected, including two persisted demo decisions after a fresh pull.

### Files changed

- `backend/app/services/audit_service.py`
- `backend/app/main.py`
- `backend/db/migrations/20260830_008_manager_activity_log.sql`
- `docker-compose.yml`
- `frontend/src/api/client.ts`
- `frontend/src/features/audit/AuditLog.tsx`
- `specs/api-contracts.md`
- `specs/frontend-screen-spec.md`
- `tests/test_backend/test_manager_activity_log.py`

### Decisions and rationale

- Kept the append-only operational audit ledger intact; only the Manager-facing Activity Log is decision-only.
- Added manager-protected `GET /api/v1/activity-log`, globally querying approve/quick-approve/reject records and joining the related approval request for its station.
- Added an idempotent migration with one approved S03 request and one rejected S02 request. It runs for fresh clones and for existing local PostgreSQL volumes after code is pulled.

### Commands/tests run and results

- `./.venv/Scripts/python.exe -m pytest tests/test_backend/test_manager_activity_log.py tests/test_backend/test_api_contract.py -q` — 9 passed.
- `npm run build` in `frontend/` — passed.
- `docker compose up -d db-migrate` — completed; migration inserted both demo approval/audit rows.
- `docker compose up -d --build backend` — completed; `/health` returned `ok`.
- Runtime: Manager and Admin sessions received the same count from `/api/v1/activity-log`; the response included the seeded S03 approval and S02 rejection.
- `ruff check` for touched backend/test files and `git diff --check` — passed.

### Next exact step

Log in as any Manager/Admin, open **Nhật ký quyết định BQL**, and verify only approval/rejection decisions are listed.

---

## Follow-up: Vietnamese ventilation labels

### Goal

Replace English/technical ventilation labels in the Manager device detail with clear Vietnamese wording, and show the approver's display name rather than an internal UUID.

### Files changed

- `backend/app/services/device_service.py`
- `backend/db/schema.sql`
- `backend/db/seed.sql`
- `backend/db/migrations/20260830_009_vietnamese_ventilation_labels.sql`
- `docker-compose.yml`
- `frontend/src/features/drawers/DeviceDetailDrawer.tsx`
- `frontend/src/types/index.ts`
- `specs/api-contracts.md`
- `tests/test_backend/test_ventilation_device_status.py`

### Decisions and rationale

- Standardized simulated device names in Vietnamese, including the existing `FILTER-01` label.
- Added the reviewer name through a backend join with `users`; retained the user ID only as internal traceability data.
- Replaced `ACK` with “Xác nhận từ thiết bị”, translated operating modes and simulator wording, and replaced the unexplained `HITL` label with “Cần BQL phê duyệt”.

### Commands/tests run and results

- `./.venv/Scripts/python.exe -m pytest tests/test_backend/test_ventilation_device_status.py -q` — 3 passed.
- `npm run build` in `frontend/` — passed.
- `ruff check` for the touched backend/test files and `git diff --check` — passed.
- `docker compose up -d db-migrate` then `docker compose up -d --build backend` — completed; migration updated existing device names. Runtime endpoint returned the Vietnamese FILTER-01 name and reviewer name.

---

## Follow-up: Manager manual simulated-filter toggle

### Goal

Allow a Manager to click **Bật máy lọc** for a stopped simulated filter or **Tắt máy lọc** for a running one, while retaining auditability and the separate automatic alert-driven ventilation flow.

### Files changed

- `backend/app/main.py`
- `backend/app/services/approval_service.py`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/features/drawers/DeviceDetailDrawer.tsx`
- `specs/api-contracts.md`
- `tests/test_backend/test_ventilation_device_status.py`

### Decisions and rationale

- Added Manager/Admin-only `POST /api/v1/devices/{id}/manual-control` with session, CSRF and idempotency enforcement.
- A click first persists a `manager_manual_device_control` proposal, then records the Manager's server-side quick approval before queuing the MQTT command. The browser never publishes MQTT directly.
- `ventilation_boost` is permitted only when stopped and `standby` only when active; ordinary automatic proposals still require the PM2.5/CO2 continuity gate and remain unchanged.

### Commands/tests run and results

- `./.venv/Scripts/python.exe -m pytest tests/test_backend/test_ventilation_device_status.py tests/test_backend/test_quick_approval.py tests/test_backend/test_person_b_api_security.py -q` — 19 passed.
- `ruff check` for the touched backend/test files and `git diff --check` — passed.
- `npm run build` in `frontend/` — passed.
- Rebuilt backend with Docker Compose. Runtime test: manual start created approved request `ad83c0f7-e6ff-4eb9-8166-d47cc9772787`, reached `RUNNING_BOOST` with `ack_status=succeeded`; manual stop then returned the same device to `STANDBY` with `ack_status=succeeded`.

---

## Follow-up: Direct Manager manual device control

### Goal

Make the Manager's manual **Bật máy lọc/Tắt máy lọc** action dispatch directly, with no approval request. Keep approval requests exclusively for automatic threshold-driven ventilation actions.

### Files changed

- `backend/app/main.py`
- `backend/app/services/device_service.py`
- `backend/app/services/approval_service.py`
- `backend/app/services/audit_service.py`
- `backend/app/tasks/notification_tasks.py`
- `backend/db/schema.sql`
- `backend/db/migrations/20260830_010_manager_manual_device_control.sql`
- `docker-compose.yml`
- `services/mqtt-consumer/mqtt_consumer/storage.py`
- `frontend/src/api/client.ts`
- `frontend/src/App.tsx`
- `frontend/src/features/drawers/DeviceDetailDrawer.tsx`
- `specs/api-contracts.md`
- `tests/test_backend/test_ventilation_device_status.py`

### Decisions and rationale

- Manager/Admin direct controls now create an audited `device_command_intent` with no `approval_request_id`, then use the existing server-side MQTT dispatcher. Session, CSRF, idempotency and state checks remain required.
- Manual controls are operational audit records, not approval decisions. Existing legacy `manager_manual_device_control` request records are hidden from the approval queue and decision-only activity log rather than deleted, preserving the append-only audit ledger.
- Automatic alert/continuity-driven ventilation proposals remain regular `pending` approval requests and are the only path that asks BQL to approve or reject.

### Commands/tests run and results

- `./.venv/Scripts/python.exe -m pytest tests/test_backend/test_ventilation_device_status.py tests/test_backend/test_quick_approval.py tests/test_backend/test_person_b_api_security.py tests/test_backend/test_manager_activity_log.py -q` - 21 passed.
- `ruff check` for touched backend/test files - passed.
- `npm run build` in `frontend/` - passed after the final client typing/wording cleanup.
- Live Manager session check: the approval API returned zero visible legacy manual-control request rows; the shared Activity Log retained the `manager_decisions` scope with 13 decision entries.
- Runtime after migration 010: direct Manager start reached `RUNNING_BOOST` with successful device acknowledgement; direct stop returned the device to `STANDBY` with successful acknowledgement. Neither new action created an approval request.

### Next exact step

Open the device drawer as Manager: a stopped filter shows **Bật máy lọc**, a running filter shows **Tắt máy lọc**, and either action sends directly to the simulator without appearing in the BQL approval queue.
