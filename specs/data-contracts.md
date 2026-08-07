
# Data Contracts

## MQTT measurement


Topic: `airguard/stations/{station_id}/measurements`.

```json
{"message_id":"MSG-S01-0001","station_id":"S01","pm25":42.5,"temperature":30.1,"humidity":72,"wind_speed":2.4,"rainfall":0,"timestamp":"2026-08-05T09:00:00+07:00","source":"simulator"}
```

<<<<<<< HEAD
Required fields: `message_id`, `station_id`, `pm25`, `timestamp`, `source`.

Optional weather fields: `temperature`, `humidity`, `wind_speed`, `wind_direction`, `rainfall`.

Validation rules for MVP:

| Field/rule | Contract |
|---|---|
| Topic station | topic station id must equal payload `station_id` |
| Station id | must exist in `data/stations.json` / `stations` master data |
| Timestamp | RFC3339 with timezone; future skew and stale threshold are config-driven |
| Source | must be `simulator` |
| PM2.5 | numeric, `0..500` |
| Temperature | optional numeric, `-20..60` |
| Humidity | optional numeric, `0..100` |
| Wind speed | optional numeric, `0..60` |
| Wind direction | optional numeric, `0..360` |
| Rainfall | optional numeric, `0..500` |
| Duplicate | `message_id` is unique; duplicate delivery is rejected/idempotently ignored |

Reject reason taxonomy: `malformed`, `unknown_topic`, `topic_station_mismatch`, `unknown_station`, `range_error`, `future_time`, `stale`, `duplicate`.

Only `valid` fresh messages enter downstream current value, alert, forecast and Agent context. Rejected MQTT messages are recorded in `mqtt_rejections` with a small payload excerpt, not raw secrets.

## MQTT station status

Topic: `airguard/stations/{station_id}/status`.

```json
{"station_id":"S01","status":"online","timestamp":"2026-08-05T09:00:00+07:00","source":"simulator","reason":"heartbeat"}
```

Required fields: `station_id`, `status`, `timestamp`, `source`. Status is `online|offline`; `reason` is optional. Backend derives stale from the last valid seen time according to configured SLA.

## Sensor simulator scenarios

`services/sensor-simulator` reads `data/stations.json` and supports `SENSOR_SCENARIO`: `normal`, `rush-hour`, `spike`, `recovery`, `duplicate`, `station-silence`. Use `SENSOR_RANDOM_SEED` for deterministic demo runs.

## Device command

Topic `airguard/devices/{device_id}/command`: command_id, device_id, action, approval_id, idempotency_key, timestamp. Dispatcher only publishes approved commands; simulator rejects all other states. Status topic returns command_id, device_id, status, timestamp, `is_simulated`.

## Tool contracts
Tools map only to backend services: current, history, compare, weather, forecast, alerts, profile, create proposal. Mutating proposal tool needs idempotency key and evidence; never retry blindly.
