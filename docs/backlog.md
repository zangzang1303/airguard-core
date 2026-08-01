# Backlog

## P0 - First Push Foundation

| ID | Task | Owner | Output | Status |
|---|---|---|---|---|
| T-001 | Update README and project summary | Team Lead | `README.md` | Done |
| T-002 | Create repo structure | Team Lead | Folder structure | Done |
| T-003 | Create station data file | Frontend/Data | `data/stations.json` | Done |
| T-004 | Run Mosquitto with Docker Compose | Data/IoT | MQTT service | Done |
| T-005 | Write PM2.5 sensor simulator | Data/IoT | `simulators/sensor_simulator` | Done |
| T-006 | Create FastAPI backend skeleton | Backend | `/health`, station APIs | Done |
| T-007 | Create database schema | Backend | `backend/db/schema.sql` | Done |
| T-008 | Create React Leaflet map prototype | Frontend | Five mock markers | Done |
| T-009 | Write API contract | Backend | `docs/api-contract.md` | Done |
| T-010 | Write user stories | Team Lead | `docs/user-stories.md` | Done |
| T-011 | Write architecture doc | Team Lead/Backend | `docs/architecture.md` | Done |
| T-012 | Design Agent tools | AI/ML | `docs/agent-tools.md` | Done |

## P1 - Demo 1 Completion

| ID | Task | Owner | Output |
|---|---|---|---|
| T-013 | MQTT Consumer saves data to PostgreSQL | Backend/Data | Measurements in DB |
| T-014 | API current/history reads from DB | Backend | REST API |
| T-015 | Frontend calls API continuously | Frontend | Live-ish dashboard |
| T-016 | Alert rule for PM2.5 threshold | Backend | Alerts |
| T-017 | Sensor offline detection | Backend/Data | Station status |
| T-018 | Improve Docker health checks and seed flow | Backend | Repeatable local setup |

## P2 - Demo 2

| ID | Task | Owner | Output |
|---|---|---|---|
| T-019 | Forecast baseline or moving average | AI/ML | Forecast API |
| T-020 | MAE/RMSE evaluation | AI/ML | Metrics report |
| T-021 | AI Agent calls backend tools | AI/ML | Agent chat endpoint |
| T-022 | HITL approval workflow | Backend | Approvals API |
| T-023 | Device simulator receives MQTT commands | Data/IoT | Device status |
| T-024 | Manager dashboard approve/reject UI | Frontend | HITL UI |
