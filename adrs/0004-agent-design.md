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

## Implementation record - 2026-08-08

AI-003 adds a versioned deterministic recommendation policy for `normal`, `sensitive` and
`outdoor_sport`. Personalized recommendations require `get_user_profile`; the graph receives
`user_id` from request context and does not infer a profile group from prose or trust a
client-supplied group. Production authentication is still an external dependency; the current
frontend identity is demo-only. Outdoor recommendations use current PM2.5, weather, forecast,
active alerts and profile results from the same request. Missing or unusable required evidence
fails closed.

The production topology exposes the root Agent as an isolated HTTP service. The system-of-record
backend keeps the canonical `/api/v1/agent/chat` endpoint and proxies the correlation id, user id
and station context. The Agent container receives a backend HTTP URL but no DB or MQTT credential.
