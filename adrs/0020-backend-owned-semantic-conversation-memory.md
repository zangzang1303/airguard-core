# ADR 0020: Backend-owned semantic conversation memory

## Status

Accepted for the simulator-backed MVP.

## Context

The chat UI previously retained bubbles only in React component state. Neither the public backend
proxy nor the isolated Agent request had a conversation identifier. Every Agent graph invocation
therefore started with only the current message, current dashboard station and map context.
Follow-up requests could not safely resolve an antecedent from a prior validated turn.

The audit proposed a LangGraph PostgreSQL/Redis checkpointer. Direct database access from the
isolated Agent would conflict with the established boundary that the backend is the system of
record and the Agent reads domain state only through backend contracts. Persisting complete graph
state would also retain raw prompts, generated prose and stale environmental values that must not
be reused as evidence.

## Decision

The public backend owns durable, bounded semantic conversation memory:

1. The public chat request and response carry an opaque UUID `conversation_id`.
2. The backend scopes each conversation to the effective authenticated/demo user and applies a
   configurable sliding TTL, defaulting to 24 hours.
3. PostgreSQL stores only allow-listed routing metadata: previous canonical intent, validated
   station IDs, primary station ID and turn count. It does not store raw prompts, answers,
   environmental values, sources, profile values, credentials or map payloads.
4. Only a successful canonical Agent outcome may update station/intent memory. Clarification,
   refusal and insufficient-data turns cannot poison a later antecedent.
5. The backend sends the bounded semantic context to the isolated Agent. The deterministic router
   may use it only for an explicit follow-up expression. Explicit station IDs in the new message
   remain authoritative; the memory is never environmental evidence.
6. Every resolved follow-up performs fresh backend tool calls. Historical AQI, PM2.5, CO2, noise,
   temperature, forecast, alert, timestamp or profile facts are never replayed from memory.
7. Social short-circuit responses remain independent of PostgreSQL, tools and the Agent. They may
   echo or allocate a conversation UUID, and the first later domain turn creates the record.
8. Starting a new conversation in the UI clears the client-side conversation UUID. Expired and
   cross-owner conversation IDs fail explicitly without disclosing another user's record.

## Alternatives considered

- LangGraph `AsyncPostgresSaver` in the Agent service: rejected because it gives the Agent direct
  PostgreSQL ownership and persists more state than antecedent resolution requires.
- Client-supplied prior messages: rejected because the client could forge history and inject
  environmental facts or another user's context.
- Process-local `MemorySaver`: rejected because state disappears on restart and is inconsistent
  across replicas.
- Store complete chat transcripts in PostgreSQL: deferred because transcript retention, deletion,
  PII policy and history UX require a separate product/privacy decision.

## Consequences

- Follow-ups such as “Còn 3 giờ tới thì sao?” can reuse the previously validated station while
  still fetching a fresh forecast.
- “So với S04 thì sao?” can combine S04 with the preceding validated station.
- The backend requires an additive table and migration for `agent_conversations`.
- This PR provides continuity, isolation and expiry, but does not provide a transcript browser.

## Verification

- Memory takes precedence over a static UI station only for recognized follow-ups.
- Missing memory still clarifies instead of guessing an antecedent.
- Failed Agent outcomes do not replace valid semantic context.
- Cross-user and expired conversation IDs are rejected.
- The Agent request schema rejects non-allowlisted stations and environmental values in memory.
- Frontend reset creates a new logical conversation.

## Owner/date

AirGuard AI team / 2026-08-27
