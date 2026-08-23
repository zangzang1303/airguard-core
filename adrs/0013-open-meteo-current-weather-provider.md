# ADR 0013: Open-Meteo current-weather provider with explicit fallback

## Status

Accepted. Supersedes ADR 0008 for environments that configure `WEATHER_API_BASE_URL`.

## Decision

Use the Open-Meteo Forecast API current-weather fields for temperature, relative
humidity, precipitation, 10 m wind speed and 10 m wind direction. Requests use UTC,
SI wind units, a short timeout and strict numeric/timestamp validation.

If the provider is not configured, times out, returns an error or violates the
response contract, return the deterministic simulator weather context with
`source=simulator_fallback_weather`, `is_fallback=true` and a non-sensitive reason.
Provider data is labelled `source=open_meteo_forecast_api`; stale provider data is
marked and remains subject to downstream data-quality gates.

## Consequences

- Local demos remain reproducible when the network is unavailable.
- Provider and fallback provenance cannot be confused in the UI or Agent.
- The provider adapter is replaceable through configuration and has no API key.
- This weather context is forecast-model data, not an official on-site observation.
