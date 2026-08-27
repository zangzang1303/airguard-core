# Data Contracts

## MQTT measurement
Topic: `airguard/stations/{station_id}/measurements`.

```json
{"message_id":"MSG-S01-0001","station_id":"S01","pm25":42.5,"temperature":30.1,"humidity":72,"wind_speed":2.4,"rainfall":0,"timestamp":"2026-08-05T09:00:00+07:00","source":"simulator"}
```

Required: message_id, station_id, pm25, timestamp, source. Consumer validates topic=id, known station, numeric range, timezone, duplicate and stale/future policy. Only `valid` fresh messages enter downstream calculations.

## Status
Topic `airguard/stations/{station_id}/status`: station_id, status `online|offline`, timestamp, source, optional reason. Backend derives stale from last valid seen according to configured SLA.

## Device command
Topic `airguard/devices/{device_id}/command`: command_id, device_id, action, approval_id, idempotency_key, timestamp. Dispatcher only publishes approved commands; simulator rejects all other states. Status topic returns command_id, device_id, status, timestamp, `is_simulated`.

## Tool contracts
Tools map only to backend services: current, history, compare, weather, forecast, alerts, profile, create proposal. Mutating proposal tool needs idempotency key and evidence; never retry blindly.
