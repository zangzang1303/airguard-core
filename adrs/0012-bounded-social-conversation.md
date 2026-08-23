# ADR 0012: Bounded social conversation before grounded domain routing

## Status

Accepted for the simulator MVP on 2026-08-23.

## Context

The geospatial service previously treated every unmatched message as a request for the best outdoor
location. Short social messages such as `ê` could therefore trigger AQI claims, recommendations and
map actions even though the user had not asked an environmental question. The product needs basic
conversation without weakening ADR 0004 grounding or making live-provider availability a demo
dependency.

## Decision

A deterministic conversation gate runs before telemetry and geospatial processing. It recognizes
greeting, acknowledgement, wellbeing, capability and farewell messages. It also distinguishes
domain questions and unknown messages. Social messages use no backend tool, environmental evidence
or map action. Unknown messages return clarification and supported AirGuard topics; they never use
the default environmental recommendation flow.

The isolated Agent service may use the configured Gemini, AgentRouter or OpenAI-compatible provider
to rewrite a locked social fallback into one or two natural Vietnamese sentences. The raw user
message is not needed in this generation prompt. A post-generation gate rejects station IDs,
measurements/units, environmental status claims, safety advice, device actions and approval
decisions. Timeout, missing provider, malformed output or policy failure preserves the deterministic
AirGuard response and is not labeled `live_llm`.

Messages that contain a social prefix plus an environmental request remain domain messages and must
follow the existing tool/evidence quality gates. Safety and HITL checks run before social routing in
the isolated Agent.

## Consequences

- Public social responses expose additive `intent` and `conversation_kind` fields with empty tools,
  evidence and map actions.
- Social phrase variants and Vietnamese normalization require regression tests.
- The deterministic fallback keeps the public demo available without provider credentials.
- Adding open-domain chat, long-term conversational memory or ungrounded general knowledge requires
  a separate decision and is outside this ADR.

## Supersedes and compatibility

This ADR extends ADR 0004 and does not relax any grounding, data-quality, safety or HITL requirement.
Existing environmental intents and response fields remain compatible.
