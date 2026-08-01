# Agent Tool Design

The AI Agent must not invent PM2.5 values. It should call backend tools and include data source and update time when available.

## Tools

```text
get_current_pm25(station_id)
get_station_history(station_id, hours)
get_weather_context()
get_pm25_forecast(station_id, hours)
get_active_alerts(station_id)
compare_stations()
get_user_profile(user_id)
create_warning_proposal(station_id, reason)
create_device_action_proposal(device_id, action, reason)
```

## Responsibilities

- Explain current PM2.5.
- Compare campus areas.
- Recommend whether users should exercise outdoors.
- Use forecast context when available.
- Create proposals for broad warnings or simulated device actions.

## Constraints

- Do not create PM2.5 data.
- Do not send broad warnings without HITL approval.
- Do not control devices without HITL approval.
- All important actions must be auditable.

## MVP Status

The current backend exposes a placeholder `/api/v1/agent/chat` endpoint. Real tool-calling and HITL enforcement are TODO.
