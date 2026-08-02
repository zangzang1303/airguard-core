# AirGuard AI

AirGuard AI is a runnable MVP for monitoring outdoor PM2.5 in a campus or small urban zone. It combines five simulated sensors, Mosquitto MQTT, FastAPI, PostgreSQL, optional Celery jobs, and a React Leaflet dashboard on OpenStreetMap.

## MVP Scope

Included:

- Five PM2.5 sensor simulators and MQTT topic design.
- FastAPI station, measurement, alert, health, and background-job APIs.
- PostgreSQL business schema and job history.
- React Leaflet map with five markers.
- Celery skeleton tasks for agent, forecast, notification, and approved device commands.
- Base Docker Compose stack plus optional `async-jobs` services.

Deferred: production AI reasoning, real forecasts/weather collection, MQTT consumer persistence, complete auth/HITL UI, and real device control.

## Architecture

```text
Sensor Simulator -> Mosquitto MQTT -> MQTT Consumer TODO -> FastAPI -> PostgreSQL
                        |                                  |
                        | approved device commands         | background jobs
                        v                                  v
                Device Simulator TODO              RabbitMQ -> Celery Worker
                                                               |       |
                                                               v       v
                                                        Redis results  PostgreSQL job_runs

React Leaflet Dashboard <---------------- FastAPI REST API
```

The default configuration uses Celery eager/in-memory mode. The backend and original APIs therefore run without RabbitMQ, Redis, or a worker.

## Infrastructure Responsibilities

- **MQTT / Mosquitto:** IoT telemetry, station status, and approved device commands. Sensor messages are not routed through Celery.
- **RabbitMQ / Celery:** coarse-grained agent, forecast, notification, and approved device-action jobs.
- **Redis:** temporary Celery task status/results.
- **PostgreSQL:** persistent stations, measurements, alerts, approvals, audit data, devices, and `job_runs`.

RabbitMQ does not replace Mosquitto.

## Background Jobs

Task modules:

- `backend/app/tasks/agent_tasks.py`
- `backend/app/tasks/forecast_tasks.py`
- `backend/app/tasks/notification_tasks.py`

`backend/app/celery_app.py` reads broker/result-backend settings from environment variables. Tasks use stable IDs derived from idempotency keys, `acks_late`, and retry with backoff/jitter for temporary network failures. The device-command task must find a matching `approval_requests.status = 'approved'` row in PostgreSQL before publishing to Mosquitto.

## Install

All local Python commands use the root `.venv`.

```powershell
python -m venv --upgrade .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r simulators\sensor_simulator\requirements.txt

cd frontend
npm.cmd install
cd ..
Copy-Item .env.example .env
```

Do not commit secrets from `.env`.

## Run Basic MVP

```powershell
docker compose up --build
```

Open dashboard at http://localhost:5173 and Swagger at http://localhost:8000/docs. MQTT uses port 1883 and PostgreSQL uses 5432.

Without Docker, run in separate terminals:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```powershell
cd frontend
npm.cmd run dev -- --host 0.0.0.0 --port 5173
```

Job APIs execute mock tasks eagerly with the default settings.

## Run Optional Async Jobs

For Demo 2:

```powershell
$env:CELERY_BROKER_URL = 'amqp://airguard:airguard@rabbitmq:5672//'
$env:CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
$env:CELERY_TASK_ALWAYS_EAGER = 'false'
docker compose --profile async-jobs up --build
```

RabbitMQ management is at http://localhost:15672. If PostgreSQL was initialized before `job_runs` was added:

```powershell
Get-Content backend\db\schema.sql | docker compose exec -T postgres psql -U airguard -d airguard
```

## Job API Examples

```powershell
$agentBody = @{
  user_id = 'demo-user'
  message = 'Explain current PM2.5 conditions'
  idempotency_key = 'agent-demo-001'
} | ConvertTo-Json

$job = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/agent/jobs -ContentType 'application/json' -Body $agentBody
Invoke-RestMethod "http://localhost:8000/api/v1/jobs/$($job.task_id)"
```

```powershell
$forecastBody = @{
  station_id = 'S03'
  hours = 3
  idempotency_key = 'forecast-s03-demo-001'
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/forecast/jobs -ContentType 'application/json' -Body $forecastBody
```

Repeating the same idempotency key returns the same logical job and `task_id`.

## Main APIs

```text
GET  /health
GET  /api/v1/stations
GET  /api/v1/stations/{station_id}/current
GET  /api/v1/stations/{station_id}/history
GET  /api/v1/alerts
POST /api/v1/agent/jobs
POST /api/v1/forecast/jobs
GET  /api/v1/jobs/{task_id}
```

## MQTT Topics

```text
airguard/stations/{station_id}/measurements
airguard/stations/{station_id}/status
airguard/devices/{device_id}/command
airguard/devices/{device_id}/status
```

## Data Model

`backend/db/schema.sql` defines `stations`, `measurements`, `weather_observations`, `alerts`, `users`, `approval_requests`, `devices`, `audit_logs`, and `job_runs`.

## References

- [Celery: First Steps](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html)
- [Celery: Tasks, idempotency, acknowledgement, and retry](https://docs.celeryq.dev/en/stable/userguide/tasks.html)
- [Celery: Configuration](https://docs.celeryq.dev/en/stable/userguide/configuration.html)

## Documents

- `docs/architecture.md`
- `docs/api-contract.md`
- `docs/backlog.md`
- `docs/agent-tools.md`
- `docs/journal/2026-08-01/README.md`
