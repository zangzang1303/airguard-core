# ADR 0009: Multi-metric environmental alerts

## Status

Accepted for the simulator MVP on 2026-08-13.

## Decision

The backend Rule Engine is the sole authority for deterministic alerts on fresh, valid, online station snapshots. It evaluates AQI, PM2.5, CO₂, noise and temperature, deduplicates an active alert by station/rule/version, and returns a rule-owned operational recommendation with the alert.

PM2.5 retains its configured consecutive-measurement gate. The other metrics use the latest accepted snapshot. Default thresholds are provisional and configured through environment variables; they must be confirmed before any non-demo use. The Agent may explain an existing alert but does not set thresholds, create an emergency declaration or bypass manager approval for an action.

## Consequences

- The alert API is the source for both threshold/result and displayed recommendation.
- UI can show multiple active alerts for one station, one per metric.
- A warning proposal remains subject to existing HITL rules.
