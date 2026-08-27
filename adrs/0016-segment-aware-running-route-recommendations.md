# ADR 0016: Segment-aware running-route recommendations

## Status

Accepted for the simulator-backed MVP.

## Context

A single station or route-wide average cannot show where exposure changes along a running route.
Drawing every recommended route with one color also hides local hotspots and can make a route look
uniformly safe. Route selection must start from the user/map origin and remain grounded in the
current or requested forecast snapshot.

## Decision

The backend owns route geometry and ranking. It snaps the validated origin to the registered road
graph, generates nearby candidates, splits each candidate polyline into short sections, and applies
distance-weighted wind-adjusted IDW to each section midpoint using request-scoped fresh station
facts. Candidate rank uses the integrated section exposure plus distance and pedestrian-safety
constraints. Only the rank-one route is highlighted as the recommendation.

The `highlight_route` map action includes the selected geometry and its environmental segments.
Each segment carries AQI, PM2.5, supporting metrics, level, contributing station ids, source and
time. The frontend only colors and labels these returned sections; it does not calculate exposure
or choose a route. Current and forecast requests are evaluated separately. Missing grounded station
coverage fails closed without route geometry.

## Consequences

- The map can show local green/yellow/orange/red sections on one selected route.
- A change in station values or forecast time may produce a different route and segment profile.
- The result remains an IDW estimate from simulated stations, not street-level certified sensing
  or a pollutant-dispersion guarantee.
- Route and frontend contract tests must verify origin precedence, dynamic ranking, segment source
  fields, time mode and map rendering compatibility.
