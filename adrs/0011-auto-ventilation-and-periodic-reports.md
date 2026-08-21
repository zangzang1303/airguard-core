# ADR 0011: HITL auto-ventilation proposals and deterministic periodic reports

## Status

Accepted for the simulator MVP on 2026-08-21. Thresholds and device operating limits remain
provisional until confirmed by the Mentor/operations owner.

## Context

Backlog 5 adds a ventilation proposal loop and daily/weekly environmental reports. These features
must preserve the existing rule-engine authority, data-quality gate, mandatory manager review,
device-dispatch boundary and grounding guarantees from ADR 0003, ADR 0009 and ADR 0010.

## Decision

The Rule Engine is the only component that qualifies an automatic ventilation trigger. A trigger is
eligible only when valid measurements from an online station show either PM2.5 strictly above
50 µg/m³ or CO₂ strictly above 1000 ppm continuously for at least 15 minutes, without a stale data
gap. The values are provisional simulator policy, not health or legal limits.

After that deterministic gate, the existing ADR 0010 live-LLM grounded analysis is still required
before creating one idempotent `pending` proposal. The canonical device actions are
`ventilation_boost`, `air_purifier_on` and `eco_mode`. The backend resolves a station to a registered
simulated device; the LLM cannot select a device. Timed actions use `duration_minutes` between 5 and
180; the default boost is 45 minutes at 80 percent.

Quick approval is only an abbreviated manager interaction. It uses the same authenticated session,
RBAC, CSRF check, expected version, idempotency protection, transactional command-intent creation
and audit trail as normal approval. It never performs automatic approval. Only the dispatcher may
publish an approved command. Device acknowledgements are correlated to the persisted command intent
and audited.

When valid measurements remain at or below both safe thresholds continuously for 20 minutes after
a successful boost, the backend may create one idempotent `pending` `eco_mode` proposal. It must not
dispatch eco mode until a manager approves it. A future policy that permits automatic recovery
dispatch requires a superseding ADR.

Daily and weekly reports persist one record per report type, timezone and half-open time range.
Quantitative statistics are calculated deterministically from PostgreSQL measurements, alerts,
proposals, command intents and device status events. An LLM may write only the narrative from the
precomputed aggregate evidence. Missing, invalid or unsupported LLM output uses a labeled
deterministic fallback without preventing report generation. Markdown, HTML and PDF exports render
the same stored report record and never recompute statistics.

## Consequences

- The proposal, command and report schemas gain additive lifecycle fields and tables.
- Fifteen-minute and twenty-minute boundary, stale/offline, duplicate review/dispatch, ACK failure,
  report idempotency and LLM-fallback tests are mandatory.
- Scheduled generation requires the optional Celery worker/beat profile; manual generation remains
  available to authenticated managers.
- Simulator data and reports retain the non-certified monitoring disclaimer.

## Supersedes and compatibility

This ADR extends, but does not weaken, ADR 0003, ADR 0009 and ADR 0010. Existing non-device warning
proposal actions remain readable for backward compatibility. No `warning_proposals` table is added;
`approval_requests` remains the system of record.
