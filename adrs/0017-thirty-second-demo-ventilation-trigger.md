# ADR 0017: Thirty-second demo ventilation trigger

## Status

Accepted for the timed MVP demo; supersedes only the 15-minute trigger duration in ADR 0011 and ADR 0015.

## Decision

The automatic ventilation eligibility window is 30 seconds in the deployed demo. The backend still requires continuously valid, fresh and online simulator measurements with PM2.5 strictly above 50 µg/m³ or CO₂ strictly above 1000 ppm. Missing, invalid, stale or offline data fails closed. The resulting proposal remains `pending` and still requires Manager approval before dispatch.

`VENTILATION_TRIGGER_SECONDS` is the canonical configuration. `VENTILATION_TRIGGER_MINUTES` remains a compatibility fallback when the seconds setting is absent. Recovery remains 20 minutes, proposal TTL remains one hour and device duration/intensity policy is unchanged.

## Rationale

A 15-minute observation window is too long for a three-minute judged demo. Thirty seconds demonstrates continuity over multiple 10-second simulator samples without reducing the workflow to a single reading.

## Consequences

This is a demo timing policy, not a health, legal or production-control recommendation. The UI and presentation must retain the simulator/non-certified disclaimer.

## Verification

Settings tests cover the 30-second default and legacy minutes fallback. Ventilation tests prove that a complete continuous 30-second window is eligible and a shorter window is rejected.
