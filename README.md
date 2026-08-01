# AirGuard AI

AirGuard AI is an MVP for monitoring outdoor PM2.5 in a small campus or urban zone. This repository focuses on a runnable prototype: simulated sensor data, MQTT topic design, a FastAPI backend, a PostgreSQL schema, and a React Leaflet dashboard with five mock stations on a real OpenStreetMap map.

## Project Overview

The demo area is VinUniversity / Vinhomes Ocean Park. Five simulated PM2.5 stations publish measurements to MQTT topics. The backend exposes basic REST APIs for station status, current readings, history, alerts, and health checks. The dashboard displays the stations as map markers with PM2.5 levels.

## Problem

People in dense urban or campus areas often do not know which outdoor zones have elevated PM2.5 at the moment they plan to commute, exercise, or spend time outside. Managers also need a simple way to see sensor status and alerts before taking wider actions.

## Proposed Solution

AirGuard AI combines PM2.5 sensor simulation over MQTT, FastAPI service APIs, PostgreSQL schema, React Leaflet map UI, and placeholder AI Agent, forecast, device, and HITL services for later milestones.

## MVP Scope

In scope for this first push:

- Five simulated PM2.5 stations.
- MQTT topics for measurements, station status, device commands, and device status.
- FastAPI APIs using mock in-memory data.
- PostgreSQL initial schema.
- React Leaflet map prototype.
- Docker Compose for backend, frontend, PostgreSQL, Mosquitto, and simulator.

Out of scope for this first push:

- Production AI Agent reasoning.
- Real weather API integration.
- Real sensor hardware.
- Real HVAC/BMS control.
- Full authentication and authorization.
- Complete HITL workflow UI.

## System Architecture

```text
Sensor Simulator -> MQTT Broker -> MQTT Consumer TODO -> FastAPI Backend -> PostgreSQL
                                      |
                                      v
                     Forecast Service TODO + Alert Engine TODO + AI Agent TODO
                                      |
                                      v
                            React Leaflet Dashboard
                                      |
                                      v
                         HITL Approval Workflow TODO
```

The current MVP runs the simulator and MQTT broker, but the backend uses mock station data until the MQTT consumer and database access layer are completed.

## Tech Stack

- Backend: FastAPI, Uvicorn, Pydantic
- Database: PostgreSQL 16
- Messaging: Eclipse Mosquitto MQTT
- Simulator: Python, paho-mqtt
- Frontend: React, Vite, React Leaflet, Leaflet
- Container orchestration: Docker Compose

## Data Model

The initial schema is in `backend/db/schema.sql` and includes `stations`, `measurements`, `weather_observations`, `alerts`, `users`, `approval_requests`, `devices`, and `audit_logs`.

## MQTT Topics

```text
airguard/stations/{station_id}/measurements
airguard/stations/{station_id}/status
airguard/devices/{device_id}/command
airguard/devices/{device_id}/status
```

## How to Run

Run everything with Docker:

```bash
docker compose up --build
```

Then open:

- Backend health: http://localhost:8000/health
- Backend API docs: http://localhost:8000/docs
- Frontend dashboard: http://localhost:5173
- MQTT broker: `localhost:1883`

Run services locally from the repository root. All Python commands use the existing root `.venv`:

```powershell
# Install Python dependencies once
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r simulators\sensor_simulator\requirements.txt

# Start MQTT and PostgreSQL
# Requires Docker Desktop
docker compose up -d postgres mqtt
```

```powershell
# Run backend from the repository root
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```powershell
# Run sensor simulator from the repository root in another terminal
.\.venv\Scripts\python.exe simulators\sensor_simulator\sensor_simulator.py
```

```powershell
# Run frontend
cd frontend
npm.cmd install
npm.cmd run dev -- --host 0.0.0.0 --port 5173
```

## API Quick Check

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/stations
curl http://localhost:8000/api/v1/stations/S01/current
curl "http://localhost:8000/api/v1/stations/S01/history?hours=6"
curl http://localhost:8000/api/v1/alerts
```

## Demo Flow

1. Start Docker Compose.
2. Open `/health` to confirm the API is alive.
3. Open `/api/v1/stations` and `/api/v1/stations/S01/current`.
4. Open the dashboard and inspect the five PM2.5 markers.
5. Watch simulator logs publish to `airguard/stations/{station_id}/measurements`.
6. Explain that MQTT consumer, DB reads, forecast, AI Agent, and HITL are planned TODO layers.

## Documents

- `docs/architecture.md`
- `docs/api-contract.md`
- `docs/user-stories.md`
- `docs/backlog.md`
- `docs/team-roles.md`
- `docs/agent-tools.md`
- `docs/journal/2026-08-01/README.md`

## Team Roles

See `docs/team-roles.md`.

## Mentor Questions

- Which demo area should be finalized before presentation?
- Should the first real integration prioritize weather data or MQTT consumer persistence?
- What PM2.5 thresholds should the team use for local health recommendations?
- What approval actions are most compelling for the HITL demo?
