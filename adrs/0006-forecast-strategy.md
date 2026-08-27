# ADR 0006: Conservative short-term forecast

## Status

Accepted for MVP.

## Decision

Forecast only 1-3 hours, using a simple baseline approved by team and optional weather context.
Every result includes model/source/generated time/freshness and confidence/limitation where
available. Forecast is advisory and never replaces current observation.

## Consequences

Low implementation risk but limited accuracy; no long-term or medical/operational certainty
claims. Replace with a new versioned model only after evaluation.

## Verification

No-data/stale/low-confidence handling, horizon bounds and Agent wording tests.

## Implementation record - 2026-08-08

AI-004 keeps observation and forecast wording separate. Forecast assessment preserves backend
station, horizon, point source, confidence, generated time, model and freshness when the typed
tool result contains them. Missing optional metadata becomes an explicit limitation instead of a
fabricated value. Low-confidence forecasts are marked uncertain and do not support a certain
trend claim. Stale forecasts fail the response quality gate.

Forecast-aware outdoor recommendations only combine current and forecast results for the same
station. Current data must be fresh and online; the forecast must be valid and not explicitly
stale.
