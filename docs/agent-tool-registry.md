# Agent Tool Registry

Registry version: `2026-08-08.ai-001`
Owner: `ai-agent`
Source of truth in code: `src/agents/tools/contracts.py`

AI Agent tools must call backend HTTP APIs only. They must not read PostgreSQL, MQTT, local sensor files, or frontend state directly. Tool input is validated before dispatch; backend output is validated before it can enter LLM context. Invalid input, backend failures, malformed JSON, and schema drift return typed tool errors.

| Tool | Backend endpoint | Mutating | Notes |
|---|---|---:|---|
| `get_current_pm25` | `GET /api/v1/stations/{station_id}/current` | no | Latest valid station measurement. |
| `get_station_history` | `GET /api/v1/stations/{station_id}/history?hours=1..72` | no | Ordered PM2.5 history. |
| `compare_stations` | `GET /api/v1/stations/{station_id}/current` per station | no | Adapter validates 2..5 unique station IDs and composes comparable current records. |
| `get_weather_context` | `GET /api/v1/weather/current` | no | VinUni/Ocean Park weather context. |
| `get_pm25_forecast` | `GET /api/v1/stations/{station_id}/forecast?hours=1..3` | no | Short-horizon forecast, distinct from observation. |
| `get_active_alerts` | `GET /api/v1/alerts?status=active&station_id={station_id}` | no | The backend performs the active-status gate; station filtering is optional. |
| `get_user_profile` | `GET /api/v1/users/{user_id}/profile` | no | Accepts backend field `user_group` and exposes Agent field `group`. |
| `create_warning_proposal` | `POST /api/v1/proposals` | yes | Maps to `ApprovalCreateRequest`, sends `Idempotency-Key`, validates `request_id` as `proposal_id`, and never retries. |

## Validation

- `station_id`: one of `S01`, `S02`, `S03`, `S04`, `S05`.
- History `hours`: integer `1..72`.
- Forecast `hours`: integer `1..3`.
- Compare station list: `2..5` unique station IDs.
- `user_id`: non-empty safe identifier, max 120 chars.
- Warning proposal: requires `user_id`, `idempotency_key`, a target station, action, rationale,
  policy version, and at least one evidence item for the same station. The AI-005 workflow requires
  both a fresh current measurement and an active alert evidence item.
- Environmental timestamps must include a timezone. Current measurements require an explicit
  `is_stale` value; weather context carries explicit `is_stale` and `is_fallback` flags. History points must be ordered
  by `measured_at`. Forecast points require a backend-provided source and either an absolute
  `forecast_at` or an hour offset, and the forecast envelope requires explicit `is_stale` freshness.
  Active-alert source metadata must come from the backend payload.
- Current PM2.5 may be `null` for a station with no usable measurement; the Agent treats that as
  insufficient data. Measurement and history sources in this simulator MVP must be `simulator`.

## Proposal Mapping

The Agent input is mapped to the backend request without exposing an approve/reject path:

```text
target.station_id -> station_id
action -> proposed_action
rationale -> reason
evidence + target + policy_version + requested_by -> evidence object
created_by -> ai_agent
idempotency_key -> Idempotency-Key header
backend request_id -> Agent proposal_id
```

Only backend status `pending` is accepted as a successful create result. The independent handoff
entry point is `run_proposal_workflow(...)` in `src/agents/nodes/proposal_workflow.py`.

## Error Mapping

Tool errors use `{ ok=false, tool_name, code, message, request_id, status_code, details }`.

| Condition | Code |
|---|---|
| Invalid tool input or backend `422` | `validation_error` |
| Backend `401` or `403` | `permission_denied` |
| Backend `404` | `not_found` |
| Backend `5xx` or transport failure | `backend_unavailable` |
| Timeout | `backend_timeout` |
| Non-JSON success response | `malformed_response` |
| JSON success response that fails output schema | `schema_drift` |

