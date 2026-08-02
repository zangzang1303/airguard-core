# Architecture

## Overview

```text
Sensor Simulator -> Mosquitto MQTT -> MQTT Consumer TODO -> FastAPI -> PostgreSQL
                        |                                  |
                        | device commands                  | background jobs
                        v                                  v
                Device Simulator TODO              RabbitMQ -> Celery Worker
                                                               |       |
                                                               v       v
                                                        Redis results  PostgreSQL job_runs

React Leaflet Dashboard <---------------- FastAPI REST API
```

## Components

- `simulators/sensor_simulator`: five-station PM2.5 telemetry.
- `mqtt`: Mosquitto for telemetry, status, and device commands.
- `backend`: FastAPI REST API and job dispatcher.
- `backend/app/tasks`: Celery agent, forecast, notification, and device-command skeletons.
- `backend/db/schema.sql`: PostgreSQL business schema.
- `frontend`: React Leaflet dashboard.
- `rabbitmq`, `redis`, `celery-worker`: optional `async-jobs` profile.

## Boundaries

- Mosquitto handles high-frequency IoT traffic and device commands.
- RabbitMQ queues coarse-grained background jobs.
- Redis stores temporary task state/results.
- PostgreSQL stores durable data, approvals, audit records, and `job_runs`.
- Sensor messages never enter Celery and RabbitMQ never replaces Mosquitto.

## Default Mode

Celery runs eagerly with memory-backed configuration by default. FastAPI does not connect to RabbitMQ or Redis during startup. The `async-jobs` profile enables real asynchronous execution for Demo 2.

## Reliability

- Stable task IDs and unique idempotency keys prevent duplicate logical jobs.
- Tasks use late acknowledgement and retry temporary network failures with backoff and jitter.
- Device commands are blocked unless PostgreSQL contains a matching approved HITL request.

## TODO

- Implement MQTT consumer persistence.
- Replace mock tasks with real agent/forecast pipelines.
- Persist approval API actions before exposing device dispatch.
- Add notification providers and production observability.
