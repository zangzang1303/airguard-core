# Agent Tool Registry

Registry version: `2026-08-04.ai-001`  
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
| `get_active_alerts` | `GET /api/v1/alerts` | no | Adapter may filter by station ID after backend response. |
| `get_user_profile` | `GET /api/v1/users/{user_id}/profile` | no | Contracted for recommendation policy; backend endpoint is not implemented yet. |
| `create_warning_proposal` | `POST /api/v1/warning-proposals` | yes | Creates `pending` proposal only; adapter does not retry this mutating call. Backend endpoint is not implemented yet. |

## Validation

- `station_id`: one of `S01`, `S02`, `S03`, `S04`, `S05`.
- History `hours`: integer `1..72`.
- Forecast `hours`: integer `1..3`.
- Compare station list: `2..5` unique station IDs.
- `user_id`: non-empty safe identifier, max 120 chars.
- Warning proposal: requires `user_id`, `idempotency_key`, target, action, rationale, policy version, and at least one evidence item. If target has `station_id`, evidence must include the same station.
- Environmental timestamps must include a timezone. Current measurements require an explicit
  `is_stale` value; weather context also carries explicit freshness. History points must be ordered
  by `measured_at`. Forecast points require a backend-provided source and either an absolute
  `forecast_at` or an hour offset. Active-alert source metadata must come from the backend payload.

## Error Mapping

Tool errors use `{ ok=false, tool_name, code, message, request_id, status_code, details }`.

| Condition | Code |
|---|---|
| Invalid tool input or backend `422` | `validation_error` |
| Backend `404` | `not_found` |
| Backend `5xx` or transport failure | `backend_unavailable` |
| Timeout | `backend_timeout` |
| Non-JSON success response | `malformed_response` |
| JSON success response that fails output schema | `schema_drift` |

