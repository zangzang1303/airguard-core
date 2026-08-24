# ADR 0015: Two-sample environmental alert gate and notification default

## Status

Accepted for the simulator MVP on 2026-08-24. This supersedes the single-snapshot portion of ADR 0009 and the default-enabled assumption in ADR 0014; it does not change the optional resident notification design.

## Decision

AQI, PM2.5, CO2, noise and temperature alerts require two consecutive valid, fresh measurements at or above the metric warning threshold. The simulator publishes every 10 seconds by default, so the normal alert confirmation window is approximately 20 seconds. AQI qualification derives each sample's AQI sub-index from its stored PM2.5 value. Missing, invalid, stale or offline data never qualifies.

`ALERT_CONSECUTIVE_MEASUREMENTS` owns the shared gate and defaults to `2`; the legacy `PM25_ALERT_CONSECUTIVE_MEASUREMENTS` remains a backend fallback for compatibility. Resident email notification is opt-in and defaults to disabled. The UI alert lifecycle remains active without email.

Automatic ventilation proposals remain separate: only qualifying PM2.5 or CO2 continuity lasting 15 minutes may create a `pending` proposal for Manager review. This decision does not allow Agent approval or device dispatch without HITL.

## Consequences

- A single transient spike does not create a metric alert.
- The five environmental metrics follow one confirmation rule.
- Local/default testing creates UI alerts without resident email jobs.
- Manager proposals cannot be created from the short two-sample alert window; they retain the 15-minute data continuity gate.

## Verification

- Unit tests cover two-sample qualification with metric-specific thresholds.
- Runtime uses a 10-second simulator interval, shared consecutive count `2`, resident notification flag `false` and ventilation trigger `15` minutes.
