# API Contracts

Base URL: `/api/v1`. JSON responses use ISO-8601 timestamps with timezone. Errors use `{ "code", "message", "request_id", "details" }` with no secret or stack trace.

## Core endpoints

| Method/path | Purpose | Success | Key errors |
|---|---|---|---|
| GET `/health` | process health | 200 | - |
| GET `/ready` | PostgreSQL readiness | 200 | 503 |
| GET `/stations` | S01-S05 latest state from PostgreSQL | 200 | 503 |
| GET `/stations/{id}` | station latest state | 200 | 404/503 |
| GET `/stations/{id}/current` | latest valid fresh measurement | 200 | 404/503 |
| GET `/stations/{id}/history?hours=1..72` | ordered valid history | 200 | 404/422/503 |
| POST `/internal/ingestion/measurements` | internal validated measurement ingestion | 202 | 404/422/503 |
| POST `/internal/ingestion/evaluate-alerts` | internal alert catch-up for one/all stations | 200 | 404/503 |
| GET `/alerts?status=&station_id=` | alert list/filter; performs rule catch-up | 200 | 422/503 |
| POST `/alerts/{id}/resolve` | manager-only manual alert resolution | 200 | 403/404/503 |
| GET `/stations/{id}/forecast?hours=1..3` | baseline forecast from fresh current PM2.5 | 200 | 404/422/503 |
| POST `/agent/chat` | placeholder grounded answer shell | 200 | 422 |
| POST `/agent/jobs` | async agent job dispatch | 202 | 422/503 |
| POST `/forecast/jobs` | async forecast job dispatch | 202 | 404/422/503 |
| GET `/jobs/{id}` | job status | 200 | 404 |
| POST `/approvals` | create pending warning proposal | 201 | 422/503 |
| GET `/approvals?status=` | manager queue | 200 | 403/503 |
| GET `/approvals/{id}` | manager detail | 200 | 403/404/503 |
| POST `/approvals/{id}/approve` | manager approve with version | 200 | 403/409/422/503 |
| POST `/approvals/{id}/reject` | manager reject with note and version | 200 | 403/409/422/503 |
| GET `/audit-logs` | manager read-only audit query | 200 | 403/503 |
| GET `/devices` | simulated device list | 200 | 503 |
| GET `/devices/{id}/status` | simulated device status | 200 | 404/503 |

## Station response

`station_id`, `station_name`, `location_type`, `latitude`, `longitude`, `description`, `active`, `pm25`, `level`, `status`, `is_stale`, `updated_at`, `last_seen_at`, `source`. PM2.5 may be null when unavailable/stale/offline; client must render state, not invent value.

## Ingestion response

Accepted measurement returns `accepted=true`, `duplicate=false`, `measurement`, and optional `alert`. Duplicate message id returns `accepted=false`, `duplicate=true`, `reason=duplicate` and must not update current/alert state.

## Approval review request

```json
{"version":1,"note":"Reviewed evidence and approved for demo dispatch."}
```

`X-User-Role: manager` is required for list/detail/approve/reject/audit. `X-User-ID` must be a UUID for review actions. Approve creates a `device_command_intents` row only when `device_id` is present. Reject never creates dispatch intent and requires a non-empty note.

## Agent tool-facing environmental responses

All environmental timestamps are ISO-8601 and timezone-aware. Current measurements and weather
context carry explicit `is_stale`; missing freshness is schema drift, not an implicit fresh value.
History items are ordered by `measured_at`. Forecast responses carry explicit `is_stale`, and each
point contains a source plus either `forecast_at` or a 1-3 hour offset. Active-alert source metadata
comes from the backend response. Stale/offline/invalid results cannot be presented as current facts.

## Agent response

`answer`, `used_tools`, `sources`, `request_id`, optional `proposal_id`. Facts must map to sources; tool failure returns a transparent insufficient-data answer.

## Compatibility


Additive fields are safe. Renaming/removing/changing meaning/status requires version plan, consumer updates, contract tests and release note.
