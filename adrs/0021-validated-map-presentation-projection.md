# ADR 0021: Validated map presentation projection

## Status

Accepted for the simulator-backed MVP.

## Context

ADR 0019 made the isolated Agent the sole authority for answer semantics and allowed the legacy
geospatial planner to run only after a grounded `spatial` answer. Two presentation gaps remained:

- route planning returned a UI-specific intent only inside `trace`, while the frontend received
  only the canonical `spatial` intent and could not render its route/indoor card;
- a grounded `compare_stations` answer intentionally skipped the route planner, so the two
  compared stations could not be highlighted on the map.

Changing the canonical intent or re-running a second conversational pipeline would reintroduce the
authority conflict fixed by ADR 0019.

## Decision

The public Agent response may expose an optional `map_intent`. It is presentation metadata only;
the canonical `intent`, answer, tools and sources remain unchanged.

Two bounded projectors are permitted:

1. An answered canonical `spatial` result with a validated same-request
   `get_spatial_air_quality` source may run the existing route/indoor map planner.
2. An answered canonical `compare` result may create station highlights, annotations and bounds
   only when every requested station appears both in the `compare_stations` tool arguments and in
   a validated same-request `compare_stations` source. Coordinates come from the backend station
   catalog and only the requested two-to-five stations are loaded.

Both projectors are best-effort. Failure preserves the grounded Agent answer and returns no map
actions. Neither projector may add environmental claims, sources, tool labels or HITL actions.

## Consequences

- The frontend can render route and indoor presentation cards without replacing the canonical
  Agent intent.
- A two-station comparison visibly highlights and frames both validated stations.
- Ordinary non-spatial intents still do not load map dependencies.
- `map_intent` and `map_actions` remain untrusted for answer grounding and must not be treated as
  evidence.

## Verification

- Spatial responses retain `intent=spatial` while exposing the planner `map_intent`.
- Comparison responses retain `intent=compare` and emit actions only for station IDs proven by
  same-request tool arguments and sources.
- Missing comparison sources fail closed with no map actions.
- Frontend build/type-check verifies propagation of `map_intent` into chat presentation state.

## Owner/date

AirGuard AI team / 2026-08-27
