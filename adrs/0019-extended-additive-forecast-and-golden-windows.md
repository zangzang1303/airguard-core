# ADR 0019: Extended additive forecast and golden air windows

## Status

Accepted. Extends ADR 0007; it does not replace the canonical 1–3 hour baseline.

## Context

The map timeline and Backlog 7 require hourly forecasts through 24 hours, uncertainty
bounds, explicit demo interactions, and a grounded way to find safe ventilation/activity
windows. The repository does not install or train the third-party Prophet package. Calling
the existing heuristic "Prophet" would misrepresent its provenance.

## Decision

- Keep `damped_linear_trend_v1` as the canonical baseline for 1–3 hours.
- Add `model=extended` for 1–24 hours using `extended_additive_fourier_v3`.
- Fit dependency-free trend plus 24h/12h Fourier components to up to seven days of hourly,
  valid simulator aggregates. The API requires at least 12 hourly points and a fresh online
  station; the spatial adapter may use its existing three-point minimum and must label the
  limitation.
- For PM2.5 only, add the versioned demo interactions from B7-01: +8.5 µg/m³ at 07:00–09:00
  and +11.0 µg/m³ at 17:00–19:00 for S01/S05; +3.5 µg/m³ at 22:00–05:00 only when humidity
  is above 80% and the projected temperature is falling.
- Derive AQI forecast points from forecast PM2.5 with the existing
  `US_EPA_PM25_24H_2012` concentration sub-index function.
- Use the 90% normal interval `prediction ± 1.645 * residual_sigma * sqrt(1 + 0.14h)`.
- A golden window is at least two contiguous hourly AQI points at or below 50 with projected
  wind at or above 2.0 m/s. If none exists, return `best_window=null`; never relax the rule.
- The Agent may query 1–24 hours through the legacy `get_pm25_forecast` name. Its adapter
  selects `baseline` through 3h and `extended` above 3h, preserving source/model/limitations.

## Consequences

The feature remains fast and deterministic for the demo and is transparent about being a
simulator-grounded heuristic rather than Prophet or an official forecast. Longer horizons
carry widening bounds and cannot drive alerts, HITL eligibility, or device commands.

## Verification

- Unit tests cover horizon bounds, uncertainty ordering, traffic/inversion gates and golden
  window continuity.
- API tests cover baseline refusal above 3h, extended 24h output and golden-window response.
- `eval/run_prophet_benchmark.py` performs a time-aligned 24h holdout over 72h simulator
  histories and records the actual pass/fail result in `docs/evidence/forecast-model-evaluation.md`.
- Frontend production build verifies the 0–24h player, golden cards and confidence chart.
