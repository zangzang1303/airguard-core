# ADR 0007: History-based short-term PM2.5 forecast

## Status

Accepted. Supersedes the constant-value baseline implementation referenced by ADR 0006.

## Decision

For the 1–3 hour MVP forecast, use the latest 3–24 valid measurements from the preceding
90 minutes at the requested station. Estimate a least-squares PM2.5 trend, damp and cap its
hourly change, and return a widening uncertainty range with a confidence score.

The endpoint returns `503 insufficient_forecast_history` if fewer than three measurements are
available. It must never substitute a repeated current value as a forecast. Outputs remain
simulator-labelled, advisory, and are not a Prophet/LSTM claim.

## Consequences

The forecast becomes responsive to sustained local movement while remaining conservative for
noisy simulator data. It needs no model-training dependency or background training job. A future
Prophet/LSTM implementation requires a new ADR, evaluation data and backtesting evidence.
