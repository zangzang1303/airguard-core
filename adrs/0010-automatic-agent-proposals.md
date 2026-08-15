# ADR 0010: Automatic Agent analysis for confirmed alerts

## Status

Accepted for the simulator MVP on 2026-08-15.

## Decision

After the backend Rule Engine confirms a fresh, valid environmental threshold alert, it schedules
an internal Agent analysis. The analysis must report `generation_mode=live_llm`; only then does the
Agent rerun its tool-grounded proposal workflow and create one idempotent `pending` warning
proposal. The trigger is not a resident chat request.

The backend alert remains the only threshold and data-quality authority. The Agent cannot approve,
reject, dispatch a command, or create a proposal for offline/stale data. Alert-to-proposal attempts,
skips and failures are audited. A `sensor_offline` alert does not qualify because it lacks the fresh
environmental evidence required for a warning proposal.

## Consequences

Managers receive evidence-backed proposals proactively. A missing/failed live LLM does not fall
back to an automatic proposal; it leaves the alert visible and records an auditable skip. The
idempotency check permits at most one proposal for an alert lifecycle at a station.
