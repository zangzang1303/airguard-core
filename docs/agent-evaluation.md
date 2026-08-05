# Agent Evaluation

## AI-002 fixture gate

Focused tests live in `tests/test_agents/test_grounding.py` and use
`FakeBackendToolClient`, so they require neither a database nor an LLM provider.

The AI-002 release gate covers:

- intent and expected tool arguments for current, history, compare, weather, forecast, alert and profile;
- mandatory tool use even when a user says not to call tools;
- source mapping for environmental facts from the same request;
- transparent handling of backend outage, empty history, stale, offline, invalid and invalid arguments;
- rejection of missing freshness, timezone-less environmental timestamps, stale weather and stale forecast;
- simulator/fixture transparency for current, history, compare, weather, forecast and alert answers;
- clarification for missing station context;
- refusal of prompt injection, medical diagnosis, emergency claims, device control and HITL bypass;
- trace request id, tool status/latency, final outcome and PII/secret redaction.

## Golden-set target

The full golden set must include current, history, compare, weather, forecast, alert, profile,
proposal, no-data, stale/offline, tool failure, injection and medical/control refusal. Each case
defines expected tools, facts allowed, forbidden claims, proposal allowed/not allowed and expected
response behavior.

Metrics: tool-selection pass, fact-to-tool grounding pass, safety pass, proposal eligibility pass,
tool-error transparency, p50/p95 latency. Critical target: 100% grounding and safety on demo cases.
Store request trace/fixture version; redact secrets/PII. Any ungrounded environmental fact blocks
demo until its regression test passes.
