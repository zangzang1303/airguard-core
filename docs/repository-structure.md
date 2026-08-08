
# Repository Structure

`backend/` FastAPI/services/jobs; `frontend/` React UI; `services/sensor-simulator/` MQTT sensor simulator; `services/mqtt-consumer/` MQTT validation and persistence service; `infra/mqtt/` broker config; `data/` non-secret seed/fixtures; `src/` legacy Agent/domain modules; `tests/` automated tests.

Documentation ownership: `specs/` contracts/product truth; `adrs/` decisions; `planning/` time/risk; `tasks/` executable work; `docs/` workflow/operations; `templates/` contribution formats. `docs/Gate 1/` is protected historical/reference material and must not be overwritten. `docs/guide/` and `docs/journal/` are reference/history, not canonical MVP contracts.

Before adding a file, choose the owning boundary; do not duplicate contracts in README or task files.
