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

## Agent tool-facing environmental responses

All environmental timestamps are ISO-8601 and timezone-aware. Current measurements and weather
context carry explicit `is_stale`; missing freshness is schema drift, not an implicit fresh value.
History items are ordered by `measured_at`. Forecast responses carry explicit `is_stale`, and each
point contains a source plus either `forecast_at` or a 1-3 hour offset. Active-alert source metadata
comes from the backend response. Stale/offline/invalid results cannot be presented as current facts.

## Agent response
`POST /api/v1/agent/chat` accepts `{ "message": string }`. The legacy
`POST /api/v1/chat` alias remains available during migration.

The response contains `answer`, `used_tools`, `sources`, `request_id`, `trace`, and optional
`proposal_id`. `sources[]` contains `tool_name` plus optional `station_id`, `observed_at`, and
`source`. `trace` contains the policy version, routed intent, per-tool status/latency and final
outcome; it must not contain the raw prompt, user id, secret, token or backend credential.
Facts must map to sources from the same request. Tool failure or absent/stale/invalid/offline data
returns a transparent insufficient-data answer and no environmental source. The additive
`response` field is a deprecated alias of `answer` for the original template client.
Every environmental answer identifies its source and states that AirGuard MVP data is not official
monitoring data; fixture or fallback sources must remain visibly labeled.

## Compatibility
Additive fields are safe. Renaming/removing/changing meaning/status requires version plan, consumer updates, contract tests and release note.
