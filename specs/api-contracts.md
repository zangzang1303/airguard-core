# API Contracts

Base URL: `/api/v1`. JSON responses use ISO-8601 timestamps with timezone. Errors: `{ "code", "message", "request_id", "details" }` with no secret/stack trace.

## Core endpoints
| Method/path | Purpose | Success | Key errors |
|---|---|---|---|
| GET `/health` | process health | 200 | - |
| GET `/ready` | dependency readiness | 200 | 503 |
| GET `/stations` | S01-S05 latest state | 200 | 503 |
| GET `/stations/{id}/current` | latest valid measurement | 200 | 404 |
| GET `/stations/{id}/history?hours=1..72` | ordered history | 200 | 404/422 |
| GET `/alerts` | alert list/filter | 200 | 422 |
| GET `/stations/{id}/forecast?hours=1..3` | forecast | 200 | 404/422 |
| POST `/agent/chat` or job endpoint | grounded answer | 200/202 | 422/503 |
| GET `/approvals` | manager queue | 200 | 403 |
| POST `/approvals/{id}/approve` | approve pending request | 200 | 403/409 |
| POST `/approvals/{id}/reject` | reject with note | 200 | 403/409 |
| GET `/jobs/{id}` | job status | 200 | 404 |

## Station response
`station_id`, `station_name`, `latitude`, `longitude`, `pm25`, `level`, `status`, `is_stale`, `updated_at`, `source`. PM2.5 may be null when unavailable; client must render state, not invent value.

## Agent response
`answer`, `used_tools`, `sources`, `request_id`, optional `proposal_id`. Facts must map to sources; tool failure returns a transparent insufficient-data answer.

## Compatibility
Additive fields are safe. Renaming/removing/changing meaning/status requires version plan, consumer updates, contract tests and release note.
