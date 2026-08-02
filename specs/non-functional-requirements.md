# Non-Functional Requirements

## Reliability
- API readiness reports DB/broker dependency state.
- Consumer handles reconnect and at-least-once duplicates idempotently.
- Invalid/stale data is observable and never contaminates downstream decisions.
- Demo startup/recovery is documented and reproducible.

## Performance
Target to confirm with team: station list under 2s local; simulator-to-UI alert under 10s at 5 stations; Agent tool response p95 under 10s excluding provider outage. Measure, do not assume.

## Security and privacy
Secrets only via environment; CORS allowlist; RBAC server-side; validation on all boundaries; redact logs/audits; no direct DB/MQTT access from frontend/Agent.

## Observability
Structured logs with request/correlation id; metrics for consumer accepts/rejects, freshness, alert lifecycle, tool failures, job failures; audit for material actions.

## Accessibility and UX
Keyboard-accessible controls, contrast-safe severity representation, responsive map/dashboard, loading/error/empty states, simulator disclaimer.

## Maintainability
Typed contracts, migrations, tests, ADR for consequential decisions, runbook and handoff log. Exact SLOs are open until Mentor/nhom confirmation.
