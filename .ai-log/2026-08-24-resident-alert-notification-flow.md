# AI Work Log

## Date / agent / machine

2026-08-24 / Codex / local Windows workspace `E:\Vinproject\P-074`

## Goal

Complete and harden the proactive flow from backend environmental alerts to resident notifications by profile group, while preserving automatic ventilation proposal HITL, device simulator ACK and audit boundaries. Leave the local stack running for user testing.

## Context read

- `AGENTS.md`, `README.md`, `tasks/backend.md`, `tasks/ai-agent.md`
- `specs/api-contracts.md`, `specs/domain-model.md`, `docs/functional-requirements.md`, `docs/test-plan.md`
- ADR 0003, 0009, 0010, 0011 and 0013
- Alert, automatic proposal, ventilation, notification, auth, device simulator and MQTT consumer implementations/tests

## Files changed

- Added resident notification orchestration service and tests.
- Added idempotent migration for `sensitive` and `outdoor_sport` demo residents.
- Updated alert evaluation to expose all simultaneous metric alerts while preserving one primary automation response.
- Extended generic notification task with subject/email type.
- Added resident notification enable/cooldown configuration.
- Restored Google OAuth success query marker expected by the frontend.
- Added ADR 0014 and updated API/domain/functional/manual-test documentation.

## Decisions and rationale

- Alert thresholds/severity stay Rule Engine-owned; profile group changes deterministic wording only.
- Notify every active, verified resident for active environmental threshold alerts; never notify resident email for resolved or sensor-offline alerts.
- Idempotency uses station, alert type, severity, resident and a configurable cooldown bucket; default 3600 seconds. Severity escalation remains independently eligible.
- Resident delivery failure is a side effect failure and cannot mutate alert/proposal/HITL state.
- Audit stores internal recipient ID/group/severity/policy only, not email or body.
- Existing singular ingestion `alert` response remains compatible; all evaluated alerts are used internally for notification coverage.

## Commands/tests run and results

- `python -m pytest -q`: `394 passed`, one ReportLab deprecation warning.
- Ruff on backend and affected tests: passed.
- `frontend/npm run build`: passed.
- `docker compose config --quiet`: passed.
- `docker compose up -d --build`: stack built and started.
- Migration `20260824_005`: exited code 0 and inserted/updated both demo group residents.
- Runtime health: backend `ok`, Agent `ok`, frontend HTTP 200, station API returned 5 stations.
- Runtime smoke IDs `runtime-resident-alert-20260824` and `runtime-resident-groups-20260824`: all five simultaneous threshold alert types were processed; audit proved notification enqueue for normal, sensitive and outdoor_sport recipients. Provider was disabled, so jobs completed `SUCCESS` with `delivery_status=not_configured` as required.
- The final runtime was deliberately left in `SENSOR_SCENARIO=spike` for user testing. At handoff the API exposed four active alerts, including S03 PM2.5 warning and AQI critical; recent audit counts covered normal, sensitive and outdoor_sport at warning and critical severity.
- In-app visual browser verification could not run because no browser instance was available; HTTP and production build checks passed.

## Contracts/risks changed

- New `RESIDENT_ALERT_NOTIFICATIONS_ENABLED` default `true`.
- New `RESIDENT_ALERT_NOTIFICATION_COOLDOWN_SECONDS` default `3600`, allowed `60..86400`.
- Production notification consent/preferences and exact health thresholds remain open; current values and wording are simulator MVP policy only.
- Real email is not enabled locally because `NOTIFICATION_PROVIDER=disabled` and Resend credentials are absent.

## Blockers/open questions

- To observe real inbox delivery, configure Resend locally. Do not commit the API key.
- Mentor/operations owner still needs to approve final thresholds, cooldown and resident notification consent policy.

## Next exact step

Open `http://127.0.0.1:5173/`, use the three demo resident personas to inspect profile-specific recommendations, then use Manager to inspect Alerts/Audit. Leave spike running for 15 minutes to exercise automatic ventilation proposal eligibility. Configure Resend only if real email delivery is required. Recreate `sensor-simulator` without the temporary process environment to return to the default normal scenario.

## Handoff IDs (request/message/proposal/job)

- Runtime correlation IDs: `runtime-resident-alert-20260824`, `runtime-resident-groups-20260824`
- Resident notification policy: `resident-alert-groups-v1`
