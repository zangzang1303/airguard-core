# ADR 0019: Task 4 closed-loop simulated ventilation and device status

## Status

Accepted for the simulator MVP on 2026-08-29. This ADR supersedes ADR 0017 and restores the
15-minute trigger window from ADR 0011.

## Context

The 30-second trigger in ADR 0017 made a short judged demo practical, but it no longer matches the
Task B7-04 continuity requirement. The manager also needs an operational map layer and the Agent
needs grounded, read-only runtime/effectiveness facts. A simulated device acknowledgement must
produce observable environmental feedback without weakening HITL.

## Decision

- Automatic `ventilation_boost` eligibility requires fresh, valid, online measurements with PM2.5
  strictly above 50 µg/m³ or CO₂ strictly above 1000 ppm continuously for 15 minutes.
- A boost remains 45 minutes at 80 percent by default. No command is published before an
  authenticated Manager/Admin approval.
- Device ACK payloads add station, action, start/end time, duration and intensity. The sensor
  simulator applies a labeled exponential decay to PM2.5 and CO₂ only for the acknowledged cycle.
- After the configured duration the simulator reports `STANDBY`. A 20-minute continuous recovery
  with PM2.5 strictly below 25 µg/m³ and CO₂ strictly below 700 ppm may create an idempotent
  `eco_mode` proposal, still pending Manager review.
- `standby` is an allow-listed device action for an audited Manager-requested safe stop. The map
  action creates a pending proposal; it does not dispatch directly.
- The Manager-only map layer renders backend device state and measured effectiveness. The Agent
  gains read-only `get_ventilation_devices_status`; it cannot approve, reject or dispatch.

## Consequences

- The demo takes at least 15 minutes to naturally qualify unless tests use an explicit configured
  shorter window. This is intentional and matches Task B7-04.
- Device and sensor payload schemas gain additive fields. Old status facts remain readable, but
  closed-loop feedback requires the new station/timing fields.
- Simulator feedback is an educational model, not evidence of real-world ventilation performance.

## Verification

Tests cover the 15-minute default, continuous-window gate, ACK-driven decay, countdown/effectiveness
shape, Agent tool grounding, Manager-only map wiring, pending Eco/Standby proposals and frontend
production build.
