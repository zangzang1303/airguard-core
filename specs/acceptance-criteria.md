# Acceptance Criteria

## Gate 05/08/2026
- Documentation tree, contracts, ADRs, tasks and run instructions are complete and internally linked.
- S01-S05 master data is seeded and simulator publishes contract-valid data with `source=simulator`.
- MQTT, backend, database and frontend can start independently; health/stations endpoints work.
- Map shows 5 stations and clearly labels source/freshness/status.
- Data validation rejects malformed/duplicate/out-of-policy messages.

## Gate 08/08/2026
- One valid measurement can be traced MQTT -> consumer -> DB -> API -> UI.
- Valid/fresh spike creates one rule-versioned alert; duplicate/stale/invalid data does not.
- Forecast is limited to 1-3h and identifies source/model/freshness.
- Agent uses backend tools, exposes tool/source trace for debug and refuses to invent missing data.
- Proposal is pending first; manager approve/reject is RBAC protected and produces audit event.
- Demo runbook is rehearsed with normal, spike, Agent and HITL scenarios.

## Failure conditions
Any secret committed, Agent hallucinated demo fact, frontend MQTT access, direct Agent DB access, unapproved device dispatch, missing audit, or simulator labeled official data blocks the gate.
