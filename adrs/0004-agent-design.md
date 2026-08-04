# ADR 0004: Tool-grounded Agent

## Status

Accepted.

## Decision

Agent uses LangGraph/tool calling with typed backend adapters. Environmental questions require tool
calls; response carries sources/used_tools in debug trace. Tool errors/no data produce transparent
insufficient-data response. System prompt and policy block hallucination, direct DB/MQTT, medical
diagnosis, approval/rejection and command control.

## Consequences

Need tool schemas, fixtures, evaluation suite and observability. Fluency never overrides missing
evidence.

## Verification

Golden cases for current/history/compare/forecast, outages, stale data, injection and proposal
eligibility.

## Implementation record - 2026-08-04

AI-002 implements a deterministic pre-LLM route and safety gate in
`src/agents/policies/grounding.py`. The graph is `route -> execute_tools -> compose -> trace`.
Only validated adapter output reaches `src/agents/response_composer.py`; direct responses are
limited to greeting, clarification, scope and safety refusal. The trace stores request id, intent,
tool status/latency, policy version and outcome without raw prompt or user profile identifiers.

AI-002 recognizes proposal intent but deliberately does not perform the mutating create call;
proposal eligibility and creation remain owned by AI-005.
