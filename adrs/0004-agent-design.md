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

## Implementation record - 2026-08-19

The live-generation boundary now supports typed `LLM_PROVIDER=auto|gemini|openai|agentrouter` configuration.
`auto` prefers Gemini, then AgentRouter/Claude, then OpenAI when the relevant key and model are present. Claude uses the Anthropic
Messages contract with bounded retry/timeout and sanitized failures; provider failure preserves the
deterministic grounded answer and cannot be reported as `live_llm`.

Recommendation policy v2 adds early indoor-protection language for `sensitive` users outside the
good band. `outdoor_sport` responses compare fresh snapshots for S01-S05 and identify the lowest-AQI
station, while selecting the lowest PM2.5 point from the requested station's fresh forecast. These
facts remain code-owned and tool-grounded; the model only appends a fact-free limitation sentence.

Gemini 3.5 Flash uses the Generate Content REST contract with `thinkingLevel=MINIMAL`, a capped
fact-free suffix, and a process-scoped HTTP client. This keeps connection setup out of repeated
requests while preserving deterministic composition, evidence sources and all safety/HITL gates.

The orchestration boundary also applies a five-second total LLM response deadline, shorter than
the backend proxy timeout. Provider HTTP retries remain bounded inside that deadline. Deadline
expiry preserves the deterministic grounded answer, records `provider_deadline_exceeded`, and is
never labeled `live_llm`.
