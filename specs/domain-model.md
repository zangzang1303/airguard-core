# Domain Model

## Entities
| Entity | Key fields | Invariants |
|---|---|---|
| Station | station_id, name, lat, lon, location_type, active | S01-S05 immutable in MVP |
| Measurement | message_id, station_id, pm25, weather, measured_at, received_at, source, validation_state | message_id unique; source simulator; timezone required |
| StationStatus | station_id, status, last_seen, stale_at | derived by backend/consumer |
| Alert | alert_id, station_id, rule_version, severity, observed, threshold, status | only valid/fresh data creates alert |
| Forecast | station_id, horizon, values, model_version, source, confidence | 1-3h; never mislabeled observation |
| UserAccount | user_id, email, email_normalized, password_hash, role, email_verified_at, is_active, lock state | email is unique case-insensitively; self-registration may only create resident accounts; password plaintext is never stored |
| UserProfile | user_id, group, role | groups normal/sensitive/outdoor_sport; profile remains backend-owned |
| UserSession | session_id, user_id, session_token_hash, expires_at, revoked_at | only a SHA-256 hash of the random opaque token is stored; expired/revoked sessions cannot authenticate |
| EmailVerificationToken | token_id, user_id, token_hash, email_normalized, expires_at, used_at | token is single-use and stored only as a hash |
| PasswordResetToken | token_id, user_id, token_hash, expires_at, used_at | token is single-use and stored only as a hash; reset must revoke existing sessions at the service layer |
| WarningProposal | id, evidence, action, status, version | pending before manager review |
| DeviceCommandIntent | command_intent_id, approval_request_id, device_id, command, status, idempotency_key | created only after approval |
| AuditLog | id, actor, action, target, outcome, correlation_id | append-only |

## Relations and lifecycle
Station 1:N Measurement, Alert, Forecast. Alert/proposal evidence points to station and measurements. UserAccount 1:N UserSession, EmailVerificationToken, PasswordResetToken; deleting a user cascades only to these authentication artifacts. Proposal: `pending -> approved|rejected`; terminal states cannot change. Alert: `active -> resolved`. Audit event is emitted for material transitions.

## Data quality state
`valid` may update current and downstream rules. `invalid`, `stale`, `offline` may be stored for diagnostics but must not drive alert/forecast/proposal. Latest current is selected by valid `measured_at`, not receive order.

## Ownership
Consumer owns ingestion/status; backend owns domain state; Agent only reads via tools and requests proposal creation; frontend renders API state.

