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
| POST `/stations/compare` | compare current fresh values for 1..5 stations | 200 | 404/422/503 |
| POST `/internal/ingestion/measurements` | internal validated measurement ingestion | 202 | 404/422/503 |
| POST `/internal/ingestion/evaluate-alerts` | internal alert catch-up for one/all stations | 200 | 404/503 |
| GET `/alerts?status=&station_id=` | alert list/filter; performs rule catch-up | 200 | 422/503 |
| POST `/alerts/{id}/resolve` | manager-only manual alert resolution | 200 | 403/404/503 |
| GET `/stations/{id}/forecast?hours=1..3` | baseline forecast from fresh current PM2.5 | 200 | 404/422/503 |
| GET `/weather/current` | weather context with explicit source/fallback | 200 | 503 |
| GET `/users/{id}/profile` | user group/profile for personalization | 200 | 404/503 |
| POST `/agent/chat` | grounded Agent response through backend-to-Agent proxy | 200 | 422/503 |
| POST `/agent/jobs` | async agent job dispatch | 202 | 422/503 |
| POST `/forecast/jobs` | async forecast job dispatch | 202 | 404/422/503 |
| GET `/jobs/{id}` | job status | 200 | 404 |
| POST `/approvals` | create pending warning proposal | 201 | 422/503 |
| POST `/proposals` | compatibility alias for pending warning proposal | 201 | 409/422/503 |
| GET `/approvals?status=` | manager queue | 200 | 403/503 |
| GET `/approvals/{id}` | manager detail | 200 | 403/404/503 |
| POST `/approvals/{id}/approve` | manager approve with version | 200 | 403/409/422/503 |
| POST `/approvals/{id}/reject` | manager reject with note and version | 200 | 403/409/422/503 |
| GET `/audit-logs` | manager read-only audit query | 200 | 403/503 |
| GET `/devices` | simulated device list | 200 | 503 |
| GET `/devices/{id}/status` | simulated device status | 200 | 404/503 |

## Station response

`station_id`, `station_name`, `location_type`, `latitude`, `longitude`, `description`, `active`, `pm25`, `level`, `status`, `freshness`, `is_stale`, `updated_at`, `last_seen_at`, `source`, `timestamp`. PM2.5 may be null when unavailable/stale/offline; client must render state, not invent value.

## Ingestion response

Accepted measurement returns `accepted=true`, `duplicate=false`, `measurement`, and optional `alert`. Duplicate message id returns `accepted=false`, `duplicate=true`, `reason=duplicate` and must not update current/alert state.

## Approval review request

```json
{"version":1,"note":"Reviewed evidence and approved for demo dispatch."}
```

`X-User-Role: manager` is required for list/detail/approve/reject/audit. `X-User-ID` must be a UUID for review actions. Approve creates a `device_command_intents` row only when `device_id` is present. Reject never creates dispatch intent and requires a non-empty note.

## Agent response
The canonical backend `POST /api/v1/agent/chat` accepts
`{ "message": string, "user_id": string, "station_id"?: "S01".."S05" }`. `user_id` is passed
to the Agent only as an argument for backend profile lookup; it is not written to Agent trace.
The current frontend identity is demo-only and does not replace production backend authentication.
`station_id` is optional dashboard context and is validated before routing. The internal Agent
service uses the same payload. The root Agent keeps the legacy `POST /api/v1/chat` alias during
migration; its `user_id` remains optional for non-personalized requests.

The response contains `answer`, `used_tools`, `sources`, `request_id`, `trace`, and optional
`proposal_id` and `recommendation_policy_version`. `sources[]` contains `tool_name` plus optional `station_id`, `observed_at`, and
`source`. `trace` contains the policy version, routed intent, per-tool status/latency and final
outcome; it must not contain the raw prompt, user id, secret, token or backend credential.
Facts must map to sources from the same request. Tool failure or absent/stale/invalid/offline data
returns a transparent insufficient-data answer and no environmental source. The additive
`response` field is a deprecated alias of `answer` for the original template client.

Recommendation intent requires current PM2.5, weather, forecast, active alerts and a backend user
profile from the same request. The client must not submit a trusted `user_group`; the Agent uses
the result of `get_user_profile`. Missing profile or environmental evidence produces clarification
or insufficient-data behavior rather than a generic personalized recommendation.

Warning proposal creation requires an active backend alert, fresh online station data and non-empty evidence. The `Idempotency-Key` request header is optional but recommended; repeated calls with the same key return the original pending request.

## Compatibility


Additive fields are safe. Renaming/removing/changing meaning/status requires version plan, consumer updates, contract tests and release note.
