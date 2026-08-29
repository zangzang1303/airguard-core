# Test Plan

## Levels

Unit: rule, validation, forecast, Agent routing/policy. Contract: MQTT schemas, API schemas, tool
adapter. Integration: simulator->broker->consumer->DB->API; alert; HITL/audit. E2E: dashboard
map/alert/chat/approval.

## Mandatory matrix

Valid, invalid, stale, offline, duplicate, out-of-order; 404/422/503; RBAC 401/403/409; provider
timeout; Agent no-data/injection; approved/rejected dispatch.

## Evidence

Record command, environment, pass/fail, request/message/proposal id, screenshot where UI. Critical
failures: hallucination, HITL bypass, secret leak, stale-data alert block merge/demo. See
agent-specific criteria in `docs/agent-evaluation.md`.

## B7-02 personalized-alert matrix

- Dose: exact 57.38 µg fixture, 7.5 ratio, duration/activity bounds, NaN/Infinity, current/forecast
  stale/offline/invalid/low-confidence.
- Route: origin boundary/snap, 1/10 km targets, 3/20 pace, at least three grounded stations,
  graph edge membership, ≤35 m samples, deterministic 70/30 ranking, comparable baseline and exact
  segment totals.
- Predictive lifecycle: one active row under concurrency, update/escalation, rolling target
  retention, two clear evaluations, observed/expiry, 30/45/60-minute lead boundaries and no late
  backfill.
- Worker/email: immediate revalidation, retry/idempotency, independent verified-resident opt-in,
  provider failure isolation, redacted audit, escaped HTML/plain text and closed deep link.
- Security/UI/Agent: RBAC, session/CSRF, checklist user scoping, unknown-field rejection, Agent reuse
  of canonical route, fail-closed response, loading/empty/error/N-A states, 375/1280 email snapshots
  and frontend build.

## B7-05 ESG report matrix

- Config/schema: policy range validation, OpenAPI integrity fields, legacy compatibility,
  idempotent migration/seed and non-overlapping profile effective ranges.
- Coverage/reference: 74.99/75 percent boundaries, half-open end exclusion, invalid/non-finite input,
  elapsed-time DST missing/repeated hours, station-day all-hour gate, QCVN always not comparable,
  WHO guideline relation and zero-denominator good-hour KPI.
- ESG: successful correlated ACK only, ordering/correlation/duration rejection, next-ACK clipping,
  profile complete-range selection, 15-minute before/final-after coverage, formula fixtures,
  aggregate rounding and complete zero versus insufficient null.
- Matrix: exactly 168 cells per view, station selector, unweighted `all_stations`, three-station and
  75 percent gates, fixed scale and explicit N/A cell/tooltip accessibility.
- Narrative/publication: typed claim allow-list, whole-response fallback for digits/URL/email/HTML or
  causal/legal/health language, stable canonical checksum, legacy export and identical ID/checksum/
  fixture values in Markdown, HTML and parsed PDF.
- API/async/UI: Manager RBAC, CSRF, pagination/format errors, lease/retry/manual-Beat reuse,
  provider fallback, React loading/empty/error/legacy/N-A states, `npm run test:reports` and build.
- Visual evidence: render the final A4 PDF with Poppler and inspect every page for Vietnamese font,
  header/footer/watermark, page break, clipping, reference disclaimer and vector matrix readability.
