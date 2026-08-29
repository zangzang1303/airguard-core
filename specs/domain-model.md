# Domain Model

## Entities
| Entity | Key fields | Invariants |
|---|---|---|
| Station | station_id, name, lat, lon, location_type, active | S01-S05 immutable in MVP |
| Measurement | message_id, station_id, pm25, weather, measured_at, received_at, source, validation_state | message_id unique; source simulator; timezone required |
| StationStatus | station_id, status, last_seen, stale_at | derived by backend/consumer |
| Alert | alert_id, station_id, rule_version, severity, observed, threshold, status | only valid/fresh data creates alert; environmental metrics require two consecutive qualifying samples by default |
| Forecast | station_id, horizon, values, model_version, source, confidence | 1-3h; never mislabeled observation |
| UserAccount | user_id, email, email_normalized, password_hash, role, email_verified_at, is_active, lock state | email is unique case-insensitively; self-registration may only create resident accounts; password plaintext is never stored |
| UserProfile | user_id, group, role | groups normal/sensitive/outdoor_sport; profile remains backend-owned and selects deterministic resident alert/recommendation wording |
| ResidentNotificationPreference | user_id, environmental_email_enabled, predictive_email_enabled, updated_at | both independent opt-ins default false; only the authenticated user may mutate them |
| UserSession | session_id, user_id, session_token_hash, expires_at, revoked_at | only a SHA-256 hash of the random opaque token is stored; expired/revoked sessions cannot authenticate |
| EmailVerificationToken | token_id, user_id, token_hash, email_normalized, expires_at, used_at | token is single-use and stored only as a hash |
| PasswordResetToken | token_id, user_id, token_hash, expires_at, used_at | token is single-use and stored only as a hash; reset must revoke existing sessions at the service layer |
| WarningProposal | id, evidence, proposed_action, device_id, duration_minutes, status, version | pending before manager review; device is resolved by backend registry |
| DeviceCommandIntent | command_intent_id, approval_request_id, device_id, command, duration_minutes, status, idempotency_key, command_id, ack status | created only after approval; at most one intent per approved proposal version |
| DeviceStatusEvent | event_id, command_id, command_intent_id, device_id, status, device_state, observed_at | simulator ACK is correlated to a persisted approved command intent |
| DeviceOperatingProfile | profile_id, device_id, profile_version, effective range, airflow/power coefficients, calibration_source, is_simulated | bounded coefficients; boost power >= eco power; half-open ranges for one device do not overlap |
| EnvironmentalReport | report_id, type, period_start/end, timezone, status, schema_version, statistics, evidence_summary, narrative, generation_mode, checksum | one deterministic record per type/range/timezone; completed v1 content has canonical SHA-256; all exports reuse it |
| PredictiveWarningEpisode | episode_id, station_id, metric, status, severity, threshold/rule/policy versions, forecast evidence, confidence, target, clear count | at most one active row per station/metric/rule; forecast advisory never creates an actual alert/HITL action |
| WarningChecklistResponse | episode_id, user_id, item_key, completed, updated_at | allow-listed self-management item; unique per episode/user/item; never dispatches a device command |
| AuditLog | id, actor, action, target, outcome, correlation_id | append-only |

## Relations and lifecycle
Station 1:N Measurement, Alert, Forecast, PredictiveWarningEpisode. Device 1:N non-overlapping DeviceOperatingProfile. Alert/proposal evidence points to station and measurements. UserAccount has one optional ResidentNotificationPreference and 1:N UserSession, EmailVerificationToken, PasswordResetToken, WarningChecklistResponse. A missing preference row is equivalent to both email flags being false. An active observed environmental alert may enqueue one resident notification only for a verified active resident with `environmental_email_enabled=true`. A predictive episode may enqueue only for `predictive_email_enabled=true` and follows `active -> observed|resolved|expired`; it never creates an actual alert, HITL proposal or device command. Proposal: `pending -> approved|rejected|expired`; terminal states cannot change. An approved device proposal creates one command intent; dispatcher publication and simulator acknowledgement are separate audited states. Successful correlated ACK intervals may join exactly one versioned device profile for report estimates. A safe 20-minute recovery window may create a new `pending` eco-mode proposal but never dispatches without Manager approval. Alert: `active -> resolved`. Report: `generating -> completed|failed`; a repeated type/range/timezone request reuses the same record. Audit event is emitted for material transitions.

## Data quality state
`valid` may update current and downstream rules. `invalid`, `stale`, `offline` may be stored for diagnostics but must not drive alert/forecast/proposal, exposure, route ranking or predictive warning. Predictive candidates additionally require a fresh forecast no older than 900 seconds with confidence at least 0.60; the lower bound, not the point estimate, gates threshold crossing. Latest current is selected by valid `measured_at`, not receive order. For the timed demo policy, auto-ventilation additionally requires a continuous valid PM2.5/CO₂ threshold window of 30 seconds; recovery requires a continuous safe window of 20 minutes. Reports aggregate only stored valid measurements and explicitly retain a simulator/non-certified disclaimer.

## Ownership
Consumer owns ingestion/status; backend owns domain state; Agent only reads via tools and requests proposal creation; frontend renders API state.

