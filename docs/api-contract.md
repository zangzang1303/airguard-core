# AirGuard AI API Contract

Base URL: `http://localhost:8000`

## Health

```http
GET /health
```

## Stations

```http
GET /api/v1/stations
GET /api/v1/stations/{station_id}
GET /api/v1/stations/{station_id}/current
GET /api/v1/stations/{station_id}/history?hours=24
```

## Weather

```http
GET /api/v1/weather/current
```

## Alerts

```http
GET /api/v1/alerts
POST /api/v1/alerts/{alert_id}/resolve
```

## Forecast

```http
GET /api/v1/stations/{station_id}/forecast?hours=3
```

## AI Agent

```http
POST /api/v1/agent/chat
```

Request:

```json
{
  "user_id": "demo-user",
  "message": "Hien tai co nen chay bo o cong vien khong?"
}
```

## HITL

```http
GET /api/v1/approvals
POST /api/v1/approvals/{request_id}/approve
POST /api/v1/approvals/{request_id}/reject
```

## Devices

```http
GET /api/v1/devices
GET /api/v1/devices/{device_id}/status
```
