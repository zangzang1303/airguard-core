# ADR 0018: Grounded deterministic automatic proposal fallback

## Status

Accepted for the simulator MVP; supersedes the live-LLM-only creation rule in ADR 0010.

## Decision

An eligible PM2.5 or CO₂ alert still invokes the Agent analysis boundary first. If the Agent returns `live_llm`, the existing tool-driven proposal flow remains unchanged. If it returns `deterministic_grounded`, the backend Automatic Proposal Service creates one idempotent `pending` proposal directly from the confirmed alert and re-runs the ventilation continuity and device-registry gates inside `ApprovalService`.

Unknown or ungrounded generation modes, Agent transport failures, stale/offline stations and failed continuity checks create no proposal. The deterministic path cannot choose thresholds, device, duration or intensity; those remain backend-owned. Manager approval is still mandatory and no command is dispatched automatically.

## Rationale

The public demo intentionally supports operation without an external LLM provider. Requiring `live_llm` made the documented deterministic grounded mode permanently unable to demonstrate the HITL queue even when all backend evidence was valid.

## Verification

Tests cover live-LLM creation, deterministic grounded creation, unknown-mode rejection, pending deduplication, evidence revalidation and notification behavior.
