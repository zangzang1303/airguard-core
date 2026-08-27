# ADR 0019: Single Agent authority and conditional map planning

## Status

Accepted for the simulator-backed MVP.

## Context

The canonical backend `POST /api/v1/agent/chat` used to invoke the isolated LangGraph Agent and
then invoke `GeospatialAgentService.process_query` for every non-social domain request. The backend
merged the Agent answer/tool trace with the legacy geospatial response after both executions.

This created two independent intent and response pipelines in one request. It also loaded the user
profile, all station snapshots and forecast histories before the authoritative Agent outcome was
known. A non-spatial answer that needed only one valid station could therefore fail because the
legacy geospatial path requires at least three usable stations. The source gate was evaluated only
after the geospatial work had already run.

## Decision

The isolated LangGraph Agent is the sole authority for `answer`, `intent`, `conversation_kind`,
`used_tools`, `tool_arguments`, `sources`, proposal fields, quality fields and the core trace.

The backend treats map planning as an optional post-processing stage:

1. It invokes the Agent exactly once.
2. It returns refusal, clarification, direct-response and insufficient-data outcomes without any
   profile, station-history or map-planner access.
3. It skips map planning for every canonical intent except `spatial`.
4. A spatial result is eligible for map planning only when it is `answered` and includes a
   validated `get_spatial_air_quality` source from the same request.
5. The planner may contribute only validated declarative `map_actions` plus bounded planner
   telemetry. Its legacy answer, intent, evidence and tool labels are never merged into the public
   Agent response.
6. Planner dependencies are loaded lazily. Planner failure yields an empty `map_actions` list and a
   sanitized trace reason; it does not replace or erase a grounded Agent answer.

The existing geospatial service remains the route-geometry implementation during this migration.
Its new map-planning boundary requires the authoritative Agent result and suppresses its own
conversational gate. A later replacement may consume the spatial tool payload directly, provided
the same authority and grounding rules remain intact.

## Alternatives considered

- Keep both complete pipelines and merge their outputs. Rejected because it preserves divergent
  intent/evidence ownership and failure coupling.
- Move all road-routing code into the isolated Agent immediately. Rejected for this PR because it
  would also move backend-owned geography/routing responsibilities and substantially expand the
  deployment contract.
- Remove map actions entirely. Rejected because route visualization is an accepted MVP feature.

## Consequences

- Normal current/history/forecast/alert/recommendation requests no longer pay for geospatial
  execution or network-wide station history reads.
- A valid single-station answer is independent of map-wide station coverage.
- Spatial text can remain available if route rendering is temporarily unavailable.
- `map_actions` are best-effort UI output; they are never evidence for the canonical answer.
- The geospatial implementation still performs request-scoped route calculations for eligible
  spatial requests and can be simplified further in a later ADR.

## Security/safety impact

The change reduces the number of components allowed to influence user-facing semantics. Missing,
stale, invalid or offline evidence still fails closed in the Agent. Map planning cannot recover a
failed Agent request, invent sources, change HITL state or expose raw tool payloads in trace.

## Contract and migration impact

The public request schema is unchanged. Non-spatial responses now always contain
`map_actions=[]`. Spatial responses receive map actions only after the source/outcome gate. The
trace adds bounded `map_planner_status` and `map_planner_reason` fields. No database migration is
required.

## Verification

- Non-spatial domain requests invoke the isolated Agent once and never invoke the map planner.
- Refusal, clarification and insufficient-data outcomes never access map dependencies.
- A current answer for one valid station succeeds when fewer than three map stations are usable.
- Spatial planning requires a validated `get_spatial_air_quality` source.
- Planner failure preserves the canonical Agent answer and produces no map action.
- Full backend, Agent and golden-set regressions remain green.

## Owner/date

AirGuard AI team / 2026-08-27
