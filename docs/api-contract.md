# AirGuard AI API Contract

Base URL: `http://localhost:8000`

## Health and Monitoring

```http
GET /health
GET /api/v1/stations
GET /api/v1/stations/{station_id}
GET /api/v1/stations/{station_id}/current
GET /api/v1/stations/{station_id}/history?hours=24
GET /api/v1/weather/current
GET /api/v1/alerts
POST /api/v1/alerts/{alert_id}/resolve
```

## Synchronous Placeholders

```http
GET  /api/v1/stations/{station_id}/forecast?hours=3
POST /api/v1/agent/chat
```

## Background Jobs

```http
POST /api/v1/agent/jobs
POST /api/v1/forecast/jobs
GET  /api/v1/jobs/{task_id}
```

Agent request:

```json
{
  "user_id": "demo-user",
  "message": "Explain current PM2.5 conditions",
  "idempotency_key": "agent-demo-001"
}
```

Forecast request:

```json
{
  "station_id": "S03",
  "hours": 3,
  "idempotency_key": "forecast-s03-demo-001"
}
```

Submission returns HTTP 202 with `task_id`, status, and `status_url`. Reusing an idempotency key returns the same logical job. Default mode executes mock tasks eagerly; `async-jobs` dispatches via RabbitMQ/Celery and uses Redis for temporary results.

## HITL and Devices

```http
GET  /api/v1/approvals
POST /api/v1/approvals/{request_id}/approve
POST /api/v1/approvals/{request_id}/reject
GET  /api/v1/devices
GET  /api/v1/devices/{device_id}/status
```

Approval APIs remain placeholders. The device-command task independently requires an approved PostgreSQL record before MQTT publish.
