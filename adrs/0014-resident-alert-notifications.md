# ADR 0014: Resident environmental alert notifications by profile group

## Status

Accepted for the simulator MVP on 2026-08-24. Environmental thresholds and notification consent remain provisional until confirmed by the Mentor/operations owner.

## Context

The Rule Engine already creates deterministic environmental alerts and the Agent/HITL loop already notifies Manager/Admin about pending device proposals. It did not notify residents when an environmental alert became active, so the resident health-profile groups affected only interactive Agent recommendations.

## Decision

After `AlertEngine` returns an active AQI, PM2.5, CO2, noise or temperature alert, the backend queues one email notification for every active, email-verified resident. The backend-owned `sensitivity_group` selects deterministic wording for `normal`, `sensitive` and `outdoor_sport`; it does not change the Rule Engine threshold, diagnose a condition or let the LLM invent advice.

The idempotency identity uses `(station_id, alert_type, severity, recipient_user_id, cooldown_bucket)`. The default cooldown is 3600 seconds and is configurable from 60 to 86400 seconds. Repeated measurements or a reopened alert lifecycle at the same severity do not resend during the bucket, while a transition from `warning` to `critical` may send one escalation. `sensor_offline`, resolved alerts and unsupported groups do not create a resident environmental notification. An unknown stored group safely uses the `normal` wording.

Notification is an optional side effect. Missing recipients, disabled/misconfigured Resend, enqueue failure or delivery failure never changes the alert lifecycle and never triggers or bypasses HITL. Audit records contain the internal recipient ID, group, severity and policy version, but never the recipient email or message body. Every message states that the data is simulator-generated and not official monitoring or medical diagnosis.

## Consequences

- Residents receive proactive, group-tailored information without granting the Agent authority over thresholds or delivery recipients.
- Manager proposal notification remains a separate flow and is still keyed by proposal and Manager/Admin recipient.
- The MVP intentionally has no notification preference/opt-out contract; production use requires consent, channel preference, rate limiting and delivery/webhook reconciliation.
- A future policy with different numeric thresholds per group requires a superseding ADR and reviewed health/safety requirements.
