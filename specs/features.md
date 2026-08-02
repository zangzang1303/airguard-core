# Features

## P0 - Foundation by 05/08
- Station catalog S01-S05 and seed.
- Sensor simulator, MQTT topics, validation and persistence.
- FastAPI health/station/current/history contracts.
- Map/list/detail with freshness/source states.
- Documentation, contract tests and basic runbook.

## P1 - MVP by 08/08
- Rule-based PM2.5 alerts with dedupe/resolve.
- Forecast 1-3h with source/model/freshness.
- Tool-grounded Agent: current/history/compare/weather/forecast/alerts/profile.
- Warning proposal, manager approval/rejection and audit log.
- Integration rehearsal and observability essentials.

## P2 - After MVP
Device simulator after HITL enforcement, richer manager UX, alert notification, forecasting improvements, CI dashboards, auth provider.

## Feature guardrails
No direct MQTT frontend; no direct DB Agent; no autonomous approval; no official-monitoring/medical claims.
