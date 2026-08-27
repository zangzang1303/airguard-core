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
| GET `/demo/station-overrides` | active demo-only station overrides; manager/admin session required | 200 | 401/403 |
| PUT `/demo/stations/{id}/override` | set demo-only PM2.5, CO₂, noise and temperature values; manager/admin session required; the backend timestamps the override so the configured continuity gate can evaluate it without rewriting measurement history | 200 | 401/403/404/422 |
| DELETE `/demo/stations/{id}/override` | remove a demo override and return to automatic simulation; manager/admin session required | 200 | 401/403 |
| GET `/stations/{id}/history?hours=1..72` | ordered valid history | 200 | 404/422/503 |
| POST `/stations/compare` | compare current fresh values for 1..5 stations | 200 | 404/422/503 |
| POST `/internal/ingestion/measurements` | internal validated measurement ingestion | 202 | 404/422/503 |
| POST `/internal/ingestion/evaluate-alerts` | internal alert catch-up for one/all stations | 200 | 404/503 |
| GET `/alerts?status=&station_id=` | alert list/filter; performs rule catch-up for AQI, PM2.5, CO₂, noise, temperature and sensor availability | 200 | 422/503 |
| POST `/alerts/{id}/resolve` | manager-only manual alert resolution | 200 | 403/404/503 |
| GET `/stations/{id}/forecast?hours=1..3&metric=pm25|aqi|co2|noise_db|temperature&model=baseline` | damped linear-trend forecast from at least 3 fresh valid measurements of the selected metric; defaults to PM2.5 and `model=baseline` | 200 | 404/422/503 |
| GET `/weather/current` | weather context with explicit source/fallback | 200 | 503 |
| GET `/spatial/heatmap?metric=aqi|pm25|co2|noise_db|temperature&forecast_hour=0..24` | grounded wind-adjusted IDW grid from at least three fresh valid online stations | 200 | 422/503 |
| GET `/users/{id}/profile` | user group/profile for personalization | 200 | 404/503 |
| PATCH `/auth/profile` | authenticated user updates own display name and recommendation group | 200 | 401/403/422/404 |
| GET `/users` | manager/admin reads persisted user accounts | 200 | 401/403/503 |
| PATCH `/users/{id}` | admin changes role and/or active status with reason, CSRF and audit | 200 | 401/403/404/409/422/503 |
| POST `/agent/chat` | grounded Agent response through backend-to-Agent proxy | 200 | 422/503 |
| POST `/agent/jobs` | async agent job dispatch | 202 | 422/503 |
| POST `/forecast/jobs` | async forecast job dispatch | 202 | 404/422/503 |
| GET `/jobs/{id}` | job status | 200 | 404 |
| POST `/proposals` | canonical Agent endpoint for pending warning proposal | 201 | 409/422/503 |
| POST `/approvals` | compatibility alias for pending warning proposal | 201 | 409/422/503 |
| GET `/approvals?status=` | manager queue | 200 | 403/503 |
| GET `/approvals/{id}` | manager detail | 200 | 403/404/503 |
| POST `/approvals/{id}/approve` | manager approve with version | 200 | 403/409/422/503 |
| POST `/approvals/{id}/quick-approve` | manager one-step approve using the same HITL checks plus idempotency key | 200 | 403/409/422/503 |
| POST `/approvals/{id}/reject` | manager reject with note and version | 200 | 403/409/422/503 |
| GET `/audit-logs` | manager read-only audit query | 200 | 403/503 |
| GET `/devices` | simulated device list | 200 | 503 |
| GET `/devices/{id}/status` | simulated device status | 200 | 404/503 |
| GET `/reports?type=daily|weekly&limit=&offset=` | manager report list | 200 | 401/403/422/503 |
| GET `/reports/{id}` | manager report detail from one persisted record | 200 | 401/403/404/422/503 |
| POST `/reports/generate` | manager manual deterministic report generation | 201 | 401/403/409/422/503 |
| GET `/reports/{id}/export?format=markdown|html|pdf` | export the same persisted report record | 200 | 401/403/404/409/422/503 |

## Station response

`station_id`, `station_name`, `location_type`, `latitude`, `longitude`, `description`, `active`, `pm25`, `aqi`, `aqi_category`, `aqi_standard`, `co2`, `noise_db`, `temperature`, `level`, `status`, `freshness`, `is_stale`, `updated_at`, `last_seen_at`, `source`, `timestamp`. AQI is the PM2.5 concentration sub-index using `US_EPA_PM25_24H_2012`; for this MVP it is computed from simulator data and is not an official AQI/NowCast. Values may be null when unavailable/stale/offline; client must render state, not invent value.

## Spatial heatmap response

`GET /spatial/heatmap` returns `metric`, `unit`, timezone-aware `timestamp` and `generated_at`,
`forecast_hour`, `source=spatial_idw_dispersion_model`, `model_version`, `model`, `extent`,
`weather`, `data_quality`, `station_inputs`, wind fields, `grid_points` and `disclaimer`.

`GET /weather/current` uses Open-Meteo current fields when configured and valid. Provider responses
are labelled `source=open_meteo_forecast_api`, include `observed_at`, `is_fallback=false` and an
explicit stale flag. Timeout, provider errors or invalid payloads return the deterministic
`simulator_fallback_weather` payload with `is_fallback=true` and a sanitized reason. See ADR 0013.
`model` records the IDW name/version, grid dimensions, power and minimum station count. `extent`
contains ordered south/west/north/east bounds. `station_inputs` preserves station id, coordinates,
value, measurement source/time and optional forecast source. `data_quality` lists required, used and
excluded stations plus exclusion reasons and sources. Weather fallback, when configured, is explicit
through `weather.source`, `is_fallback`, `observed_at` and assumptions; stale weather is rejected.

Interpolation requires at least three geographically distinct, fresh, valid and online station
snapshots. Empty data or insufficient coverage returns `insufficient_spatial_data` with HTTP 503.
An unavailable station snapshot store returns `spatial_station_data_unavailable` with HTTP 503.
Invalid metric or forecast horizon returns the standard structured 422 error. The frontend and Agent
must not generate substitute grid points, intensity, station values or provenance.

Station list, current, history, comparison and forecast endpoints fail closed when PostgreSQL data
is unavailable or forecast history is insufficient. They never replace missing, stale or failed
system-of-record reads with an in-memory simulator snapshot. The `timestamp` returned by
`/stations/{id}/current` is the measurement observation time, not the API request time. Frontend
clients must show loading, empty or retryable error states instead of rendering fixture values as live.

## Short-term forecast response

The canonical Agent forecast is the `baseline` model only, for 1–3 hours and `metric=aqi|pm25`.
Its response preserves `station_id`, `metric`, `horizon_hours`, timezone-aware `generated_at`,
`model_name`, `model_version`, `source`, `freshness="fresh"`, `is_stale=false`, numeric
`confidence`, `limitations`, and ordered `items`. Each item has `hour`/`hour_offset`, timezone-aware
`forecast_at`, `value` (or complete `value_min`/`value_max`), numeric `confidence`, and `source`.
The Agent may accept the legacy PM2.5 field aliases from this endpoint only during typed validation;
it must not infer a source, timestamp, value, freshness, or metadata that is absent. A 24-hour/cả ngày
request is refused by the Agent without a tool call because it is outside the MVP forecast contract.

## Environmental alert response

Each alert includes `alert_type` (`aqi_threshold`, `pm25_threshold`, `co2_threshold`, `noise_threshold`, `temperature_threshold` or `sensor_offline`), `severity`, observed and threshold values, title/description, source and lifecycle timestamps. Environmental threshold alerts additionally expose `metric`, `unit` and a deterministic `recommendation`; UI must render these values and must not infer its own thresholds or recommendation. Rules evaluate only valid, fresh and online simulator data. AQI, PM2.5, CO2, noise and temperature require `ALERT_CONSECUTIVE_MEASUREMENTS` consecutive samples at or above the metric warning threshold (default `2`); AQI derives the sub-index for each stored PM2.5 sample. The configured thresholds are provisional MVP defaults, not health or legal limits.

## Automatic Agent proposal

When `AUTO_PROPOSAL_ENABLED=true`, a newly eligible environmental alert schedules exactly one
canonical internal Agent proposal workflow. It uses `generation_mode=deterministic_grounded` with
`llm_call_count=0`, revalidates fresh station data plus the active alert through backend tools, and
only then may create a `pending` proposal. Only one pending
automatic warning proposal is permitted per station; later automatic triggers are skipped until the
Manager reviews it. Pending proposals automatically expire after `PROPOSAL_PENDING_TTL_SECONDS`
(default: 3600 seconds); expiry preserves the proposal and writes an audit event, but it can no
longer be approved or dispatched. No Manager decision or device command is automated. Tool error,
missing/stale/offline/invalid data, an inactive alert or failed eligibility are audited and leave the
alert active without a proposal or notification.

For a focused demo, `AUTO_PROPOSAL_STATIONS=S03` matches the `spike` scenario and registered `FILTER-01` device.
Other stations may still produce backend alerts, but their alerts do not schedule Agent proposals.

For auto ventilation, only `pm25_threshold` and `co2_threshold` alerts qualify. The Rule Engine must
also prove a continuous valid/fresh window longer than or equal to 30 seconds with PM2.5 strictly
above 50 µg/m³ or CO₂ strictly above 1000 ppm. The canonical action is
`ventilation_boost`; the backend resolves `device_id` from its device registry and applies the
default `duration_minutes=45` and `intensity_percent=80`. LLM output cannot choose a device,
threshold, duration or intensity. The additive device action allow-list is
`ventilation_boost|air_purifier_on|eco_mode`; timed actions accept 5..180 minutes. Existing
non-device warning actions remain readable for compatibility.

After a successfully acknowledged boost, a continuous 20-minute valid window at or below both safe
thresholds may create one idempotent `pending` `eco_mode` proposal. It still requires Manager
approval and never dispatches automatically.

## Ingestion response

Accepted measurement returns `accepted=true`, `duplicate=false`, `measurement`, and optional `alert`. Duplicate message id returns `accepted=false`, `duplicate=true`, `reason=duplicate` and must not update current/alert state.

History items include `message_id`, `station_id`, `measured_at`, `received_at`, PM2.5/weather fields, `source` and `quality_flag`. `measured_at` is the simulator observation time; `received_at` is the backend/consumer ingestion time.

## Approval review request

```json
{"version":1,"note":"Reviewed evidence and approved for demo dispatch."}
```

`X-User-Role: manager` is required for list/detail/approve/reject/audit. `X-User-ID` must be a UUID for review actions. Approve creates a `device_command_intents` row only when `device_id` is present. Reject never creates dispatch intent and requires a non-empty note.

The authenticated implementation derives identity and role from the HttpOnly session; legacy
identity headers are not trusted. Approve, quick-approve, reject and report generation require the
double-submit CSRF token. Quick approve uses the same JSON body and additionally requires an
`Idempotency-Key` header of at least eight characters. A retry with the same key returns the original
approved result and must not create or publish a second command. A stale version or a different key
after review returns `409`.

Ventilation proposal/approval responses add `device_id`, canonical `proposed_action`, optional
`duration_minutes`, optional `intensity_percent`, `review_mode` and the command intent state. MQTT
publication and device acknowledgement are separate states. The dispatcher persists `command_id`;
the consumer correlates the simulator status event to that command and audits success, rejection or
failure. UI must not show `RUNNING_BOOST` until the acknowledged device state is returned.

Creating an automatic ventilation or recovery proposal enqueues at most one Manager notification
per active Manager/Admin recipient, keyed by `(proposal_id, recipient_user_id)`. Notification is an
optional side effect: unavailable recipients, disabled Resend provider, broker enqueue failure or delivery
failure must be recorded transparently and must not approve, reject, delete or otherwise mutate the
persisted `pending` proposal. Audit details identify the recipient by internal user id and must not
contain the email address. Task results and worker logs must omit both recipient address and message
body. A real email is sent only when `NOTIFICATION_PROVIDER=resend` and valid Resend API settings are
configured (yielding `delivery_status=accepted` with message ID); otherwise the job completes with `delivery_status=not_configured`.

When `RESIDENT_ALERT_NOTIFICATIONS_ENABLED=true` and the Rule Engine returns an active AQI, PM2.5, CO2, noise or temperature alert, the backend also
queues at most one resident notification per `(station_id, alert_type, severity, recipient_user_id,
cooldown_bucket)`. The default cooldown is 3600 seconds. Recipients
are active, email-verified users whose backend role is `resident`. The stored `sensitivity_group`
selects deterministic wording for `normal`, `sensitive` or `outdoor_sport`; alert thresholds and
severity remain Rule Engine-owned and are not changed by the notification layer. A severity
escalation may enqueue one additional message, while repeated samples or a reopened alert lifecycle
at the same severity are idempotently reused during the cooldown. Resolved and sensor-offline alerts do not send resident environmental email.
Messages retain the simulator/non-certified disclaimer. Notification failure does not mutate the
alert or any proposal/HITL state, and audit metadata must not contain recipient email or body. The
resident email flag defaults to `false`; UI alerts continue to work while it is disabled.


## Environmental report request and response

Manual generation accepts:

```json
{
  "type": "daily",
  "period_start": "2026-08-20T00:00:00+07:00",
  "period_end": "2026-08-21T00:00:00+07:00",
  "timezone": "Asia/Ho_Chi_Minh"
}
```

`period_start` and `period_end` must both be omitted or both be timezone-aware. When omitted, daily
generation uses the last completed local day and weekly generation uses the last completed
Monday-to-Monday week. The identity `(type, period_start, period_end, timezone)` is idempotent;
repeated manual or scheduled generation reuses the persisted record.

Each report contains `report_id`, `report_type`, half-open time range, `timezone`, generation
`status`, deterministic `statistics`, `evidence_summary`, `narrative`, `generation_mode`,
`model_source`, timestamps and an optional sanitized `failure_code`. Statistics include valid and
excluded sample counts, per-station AQI/PM2.5/CO₂/noise/temperature aggregates, daily trend,
weekday/weekend comparison, alert/proposal counts, acknowledged ventilation activation duration and
before/after effectiveness. AQI is derived by backend policy from stored PM2.5; quantitative values
never come from the LLM.

The optional narrative provider receives aggregate evidence only. A response is accepted as
`generation_mode=live_llm` only when it satisfies the grounded narrative contract. Missing,
timed-out, malformed or unsafe provider output stores a `deterministic_grounded` narrative and a
sanitized fallback reason without failing the statistics report. All report records retain the
simulator/non-certified disclaimer and contain no raw prompt, secret, session token, email or user
profile. Markdown, HTML and PDF exports render the same stored record; they never recalculate data.

## Agent response
The canonical backend `POST /api/v1/agent/chat` accepts
`{ "message": string, "user_id": string, "station_id"?: "S01".."S05", "map_context"?: object }`. For an anonymous
Demo Day request, `user_id` is passed to the Agent only as an argument for backend profile lookup; it is not written to
Agent trace. For an authenticated request, backend replaces this field with the session user ID before profile lookup.
The current frontend identity is demo-only and does not replace production backend authentication.
`station_id` is optional dashboard context and is validated before routing. The internal Agent
service uses the same payload. The root Agent keeps the legacy `POST /api/v1/chat` alias during
migration; its `user_id` remains optional for non-personalized requests.

The response contains `answer`, `intent`, `conversation_kind`, `used_tools`, `tool_arguments`,
`sources`, `map_actions`, `request_id`, `trace`, and optional
`proposal_id`, `recommendation_policy_version`, and `impact_policy_version`. The impact intent
uses a fresh station snapshot and rates operational environmental impact with AQI as the primary
index; PM2.5, CO₂, noise and temperature are supporting evidence only. It is not a medical
diagnosis or emergency declaration. `sources[]` contains `tool_name` plus optional `station_id`, `observed_at`, and
`source`. `trace` contains the policy version, routed intent, per-tool status/latency and final
outcome; it must not contain the raw prompt, user id, secret, token or backend credential.
Facts must map to sources from the same request. Tool failure or absent/stale/invalid/offline data
returns a transparent insufficient-data answer and no environmental source. The additive
`response` field is a deprecated alias of `answer` for the original template client.

The internal Agent service exposes `GET /api/v1/metrics` for bounded operational monitoring. The
response contains aggregate request counts, generation-mode counts, total LLM call count,
sanitized failure-code counts, fallback rate, a rolling window of P50/P95/P99 request latency, and
alert reason codes. It must not
contain prompts, user IDs, request IDs, station evidence, sources, tokens, credentials or PII. The
current in-process window is diagnostic for a single Agent process and resets when that process is
restarted; production multi-replica aggregation belongs in the deployment metrics backend.

The direct geospatial response path receives fresh station snapshots and forecast histories from
the backend request scope. It must return structured `503` when grounded inputs are unavailable and
must not synthesize AQI, PM2.5, CO₂, noise, temperature, timestamp or a default user profile in an
exception handler. Within `POST /agent/chat`, geospatial planning is optional UI post-processing:
planner unavailability returns the already-grounded Agent answer with `map_actions=[]` and a
sanitized planner status instead of converting that answer into a `503`.

Basic social messages are intercepted before profile, geospatial, telemetry or LLM access. Their
response adds `conversation_kind`, has empty `used_tools`, `tool_arguments`, `sources`/`evidence`
and `map_actions`, and omits current/forecast time context. The response is the locked deterministic
social fallback; no configured LLM may rewrite it. Unknown messages return `clarification` instead
of falling through to a default environmental recommendation.

Recommendation intent requires current PM2.5, weather, forecast, active alerts and a backend user
profile from the same request. The client must not submit a trusted `user_group`; the Agent uses
the result of `get_user_profile`. Missing profile or environmental evidence produces clarification
or insufficient-data behavior rather than a generic personalized recommendation.

The public backend proxy must use the isolated Agent response as the authority for `answer`,
`intent`, `conversation_kind`, `used_tools`, `tool_arguments`, `sources`, proposal/quality fields
and the core `trace`; it must not infer tool names from intent. The proxy invokes the Agent exactly
once. Deterministic map planning is skipped for non-spatial, refused, clarification,
direct-response and insufficient-data outcomes. It may add only route geometry and declarative map
actions after an `answered` canonical `spatial` result returns a validated
`get_spatial_air_quality` source from the same request. Planner output must not replace the Agent
answer, evidence, intent or tool trace. Planner dependency failure preserves the Agent answer,
returns `map_actions=[]` and records only a sanitized planner status/reason. A map-wide running/area
request without a station id uses `get_spatial_air_quality` instead of inventing a default station.

For running-route intents, the planner resolves the request origin in this order: explicit map
selection, named POI, current map selection, GPS user location, then the labelled demo default.
It evaluates candidate road-network polylines using distance-weighted environmental exposure at
short route segments. The selected `highlight_route` action contains `coordinates`, `segments`,
`distance_km`, `rank=1`, `data_mode`, `observed_at` and `source`. Each segment contains exactly two
coordinates, distance, AQI, PM2.5, CO2, noise, temperature, level, source station ids and timestamp.
The frontend colors those returned segments independently; it must not recompute pollution or
choose a different route. Current and forecast requests produce separate segment profiles from the
corresponding request-scoped station data. Missing grounded station coverage returns `503` and no
route geometry.

## Administrative user mutation

`PATCH /api/v1/users/{id}` is Admin-only, requires CSRF and accepts a non-empty `reason` plus
optional `role` (`resident`, `manager`, `admin`) and/or `status` (`active`, `disabled`). The backend
prevents self-mutation and removal of the last active Admin, revokes active sessions when disabling
an account, and writes `user.admin_updated` in the same database transaction. The response contains
the persisted `user` and its `audit` record. Invitation lifecycle is not part of this endpoint.

## Authenticated profile update

`PATCH /api/v1/auth/profile` requires a valid session and CSRF token. It accepts optional
`full_name` (1–150 characters) and/or `sensitivity_group` (`normal`, `sensitive`, `outdoor_sport`), and returns
`{ "user": { "user_id", "email", "role", "full_name", "sensitivity_group", "is_active" } }`.
It updates only the authenticated account, produces `auth.profile_updated` audit metadata, and does not accept
medical diagnoses, age, child/elderly flags, or notification preferences.

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
