# ADR 0019: Independent notification consent and predictive-warning episodes

## Status

Accepted for `b7-personalized-alerts-v1` on 2026-08-29.

## Context

ADR 0014 allowed deterministic resident email for observed environmental alerts but intentionally
had no per-user preference. Task B7-02 also needs forecast-based advisory notifications without
turning a forecast into an actual alert, HITL proposal, or device command.

## Decision

Resident email consent is backend-owned and split into two opt-ins:
`environmental_email_enabled` and `predictive_email_enabled`. Both default to `false`, including
existing users. Preference changes require an authenticated session, double-submit CSRF, strict
boolean fields, and a redacted audit record. This supersedes only the no-opt-out portion of ADR 0014.

Predictive warnings use a separate versioned episode state machine:
`active -> observed|resolved|expired`. A station/metric/rule version has at most one active episode.
Candidates require a fresh valid online simulator current snapshot and a fresh baseline forecast
whose confidence and age pass policy. The earliest 1-2 hour point whose lower bound reaches the
configured PM2.5 threshold owns the target. An active actual PM2.5 alert transitions the episode to
`observed`; it never causes a predictive email.

Celery Beat evaluates every 15 minutes. Notification jobs are admitted only in the configured
30-60 minute lead window and revalidate all gates immediately before delivery. Delivery is
idempotent by episode, severity, and internal recipient user ID. Failure or retry does not mutate
alert, proposal, HITL, or device state. Audit and worker logs omit email addresses and message bodies.

Email deep links are backend-generated from `FRONTEND_URL`, an allow-listed station ID and episode
UUID. They contain no token, GPS, return URL, tracking pixel, or mutation action. Checklist writes
remain authenticated, CSRF-protected, and scoped to the session user.

## Consequences

- Environmental and predictive email can be enabled independently and remain disabled by default.
- Forecast warnings are advisory records, not observed alerts or emergency declarations.
- Async workers must have the same threshold/freshness policy configuration as the API.
- Resend `accepted` means provider acceptance only, not inbox delivery.

## Verification

Migration/default opt-out, preference RBAC/CSRF, concurrent episode creation, lower-bound and
confidence/freshness gates, lead-window boundaries, worker revalidation, retry/idempotency,
redaction, HTML escaping, exact deep-link, and provider-failure tests.
