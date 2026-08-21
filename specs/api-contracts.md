# API Contracts

## Authentication foundation status

The database contains additive storage for case-normalized user email, account status,
login sessions, email-verification tokens and password-reset tokens. Raw session and
action tokens must never be persisted; services store only their SHA-256 hashes.

Authentication endpoints are not enabled by this schema change. Until a later contract
introduces authenticated sessions and server-derived roles, the existing frontend identity
and `X-User-ID`/`X-User-Role` behavior remain demo-only and must not be represented as
production authentication.

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
| GET `/alerts?status=&station_id=` | alert list/filter; performs rule catch-up for AQI, PM2.5, CO₂, noise, temperature and sensor availability | 200 | 422/503 |
| POST `/alerts/{id}/resolve` | manager-only manual alert resolution | 200 | 403/404/503 |
| GET `/stations/{id}/forecast?hours=1..3&metric=pm25|aqi|co2|noise_db|temperature` | damped linear-trend forecast from at least 3 fresh valid measurements of the selected metric; defaults to PM2.5 | 200 | 404/422/503 |
| GET `/weather/current` | weather context with explicit source/fallback | 200 | 503 |
| GET `/users/{id}/profile` | user group/profile for personalization | 200 | 404/503 |
| POST `/agent/chat` | grounded Agent response through backend-to-Agent proxy | 200 | 422/503 |
| POST `/agent/jobs` | async agent job dispatch | 202 | 422/503 |
| POST `/forecast/jobs` | async forecast job dispatch | 202 | 404/422/503 |
| GET `/jobs/{id}` | job status | 200 | 404 |
| POST `/proposals` | canonical Agent endpoint for pending warning proposal | 201 | 409/422/503 |
| POST `/approvals` | compatibility alias for pending warning proposal | 201 | 409/422/503 |
| GET `/approvals?status=` | manager queue | 200 | 403/503 |
| GET `/approvals/{id}` | manager detail | 200 | 403/404/503 |
| POST `/approvals/{id}/approve` | manager approve with version | 200 | 403/409/422/503 |
| POST `/approvals/{id}/reject` | manager reject with note and version | 200 | 403/409/422/503 |
| GET `/audit-logs` | manager read-only audit query | 200 | 403/503 |
| GET `/devices` | simulated device list | 200 | 503 |
| GET `/devices/{id}/status` | simulated device status | 200 | 404/503 |

## Station response

`station_id`, `station_name`, `location_type`, `latitude`, `longitude`, `description`, `active`, `pm25`, `aqi`, `aqi_category`, `aqi_standard`, `co2`, `noise_db`, `temperature`, `level`, `status`, `freshness`, `is_stale`, `updated_at`, `last_seen_at`, `source`, `timestamp`. AQI is the PM2.5 concentration sub-index using `US_EPA_PM25_24H_2012`; for this MVP it is computed from simulator data and is not an official AQI/NowCast. Values may be null when unavailable/stale/offline; client must render state, not invent value.

## Environmental alert response

Each alert includes `alert_type` (`aqi_threshold`, `pm25_threshold`, `co2_threshold`, `noise_threshold`, `temperature_threshold` or `sensor_offline`), `severity`, observed and threshold values, title/description, source and lifecycle timestamps. Environmental threshold alerts additionally expose `metric`, `unit` and a deterministic `recommendation`; UI must render these values and must not infer its own thresholds or recommendation. Rules evaluate only valid, fresh and online simulator data. The configured thresholds are provisional MVP defaults, not health or legal limits.

## Automatic Agent proposal

When `AUTO_PROPOSAL_ENABLED=true`, a newly eligible environmental alert schedules an internal
Agent analysis. The Agent must report `generation_mode=live_llm` and revalidate fresh station data
plus the active alert through backend tools before it creates a `pending` proposal. Only one pending
automatic warning proposal is permitted per station; later automatic triggers are skipped until the
Manager reviews it. Pending proposals automatically expire after `PROPOSAL_PENDING_TTL_SECONDS`
(default: 3600 seconds); expiry preserves the proposal and writes an audit event, but it can no
longer be approved or dispatched. No Manager decision or device command is automated. A failed/missing LLM is
audited and leaves the alert active without a proposal.

For a focused demo, `AUTO_PROPOSAL_STATIONS=S05` restricts automatic proposal creation to S05.
Other stations may still produce backend alerts, but their alerts do not schedule Agent proposals.

## Ingestion response

Accepted measurement returns `accepted=true`, `duplicate=false`, `measurement`, and optional `alert`. Duplicate message id returns `accepted=false`, `duplicate=true`, `reason=duplicate` and must not update current/alert state.

History items include `message_id`, `station_id`, `measured_at`, `received_at`, PM2.5/weather fields, `source` and `quality_flag`. `measured_at` is the simulator observation time; `received_at` is the backend/consumer ingestion time.

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
`proposal_id`, `recommendation_policy_version`, and `impact_policy_version`. The impact intent
uses a fresh station snapshot and rates operational environmental impact with AQI as the primary
index; PM2.5, CO₂, noise and temperature are supporting evidence only. It is not a medical
diagnosis or emergency declaration. `sources[]` contains `tool_name` plus optional `station_id`, `observed_at`, and
`source`. `trace` contains the policy version, routed intent, per-tool status/latency and final
outcome; it must not contain the raw prompt, user id, secret, token or backend credential.
Facts must map to sources from the same request. Tool failure or absent/stale/invalid/offline data
returns a transparent insufficient-data answer and no environmental source. The additive
`response` field is a deprecated alias of `answer` for the original template client.

Recommendation intent requires current PM2.5, weather, forecast, active alerts and a backend user
profile from the same request. The client must not submit a trusted `user_group`; the Agent uses
the result of `get_user_profile`. Missing profile or environmental evidence produces clarification
or insufficient-data behavior rather than a generic personalized recommendation.

Warning proposal creation requires an active backend alert, fresh online station data and non-empty
evidence. The canonical Agent request maps to `ApprovalCreateRequest`:

```json
{
  "request_type": "warning_proposal",
  "station_id": "S02",
  "proposed_action": "notify_station_area_users",
  "reason": "Fresh simulator PM2.5 data and an active backend alert require manager review.",
  "evidence": {
    "items": [],
    "target": {"audience": "station_area", "station_id": "S02"},
    "policy_version": "2026-08-08.ai-005",
    "requested_by": "demo-user",
    "expires_at": null
  },
  "created_by": "ai_agent"
}
```

The Agent sends its deterministic idempotency key in the `Idempotency-Key` header. Repeated calls
with the same key return the original pending request. Backend `request_id` is exposed to the Agent
as `proposal_id`; only status `pending` is a successful Agent create result. Mutating create calls
must not be retried automatically.

## Compatibility


Additive fields are safe. Renaming/removing/changing meaning/status requires version plan, consumer updates, contract tests and release note.
