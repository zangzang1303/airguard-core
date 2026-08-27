# ADR 0014: Deterministic automatic proposal workflow

## Status

Accepted on 2026-08-27. Supersedes ADR 0010 for automatic warning proposals.

## Context

ADR 0010 required a provider-backed analysis before a second Agent request created a proposal. That analysis duplicated the canonical workflow's data and alert checks.

## Decision

An eligible backend alert schedules exactly one canonical Agent proposal request. The deterministic grounded proposal workflow obtains current station data and active alerts from backend tools, applies freshness, online, validity and eligibility gates, and creates only an idempotent `pending` proposal when every gate passes. It has zero logical LLM invocations and does not depend on a provider key.

The worker never parses answer text. It audits a stable reason when no proposal id returns, and notifies only after a pending proposal persists. Manager review and server-side dispatch remain unchanged.

## Consequences

One alert attempt has one Agent invocation rather than two. Tool error, missing/stale/offline/invalid data, no active alert and ineligibility create no proposal, notification, approval or dispatch, and leave auditable evidence.

## Security/safety impact

Grounding remains backend-tool-only; thresholds, device, duration and intensity remain policy-owned. HITL is preserved because every successful proposal stays `pending` for a Manager.

## Contract and migration impact

No public request shape changes. Trace `llm_call_count` means logical model invocation, not provider HTTP attempts.

## Verification

Hermetic tests cover the real proposal graph with fake backend tools, tool failure, pending creation, notification gating and audit outcomes.

## Owner/date

AirGuard team, 2026-08-27.
