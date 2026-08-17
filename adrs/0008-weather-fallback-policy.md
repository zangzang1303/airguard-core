# ADR 0008: MVP weather fallback policy

## Status

Accepted for MVP demo; external weather provider deferred.

## Decision

Use the deterministic simulator fallback for weather context in the MVP. The backend must label it with `source=simulator_fallback_weather` and `is_fallback=true`; it must not be described as live, official, or certified weather data.

## Rationale

The demo does not yet have a confirmed provider, API-key owner, rate-limit policy, or external-service failure contract. A deterministic fallback keeps the demo reproducible and preserves the backend weather contract.

## Consequences

- Weather responses remain available locally with explicit provenance and freshness.
- Provider timeout, rate-limit, stale-cache, and missing-key behavior are deferred until an external provider is selected.
- A future provider adapter must preserve `source`, `observed_at`, `is_fallback`, and `is_stale` fields and add its own failure tests before replacing the fallback.
