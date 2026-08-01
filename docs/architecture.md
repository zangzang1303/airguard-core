# Architecture

## Overview

```text
Open-Meteo Weather API TODO
        |
        v
Weather Collector TODO
        |
        v
Sensor Simulator -> MQTT Broker -> MQTT Consumer TODO -> FastAPI Backend -> PostgreSQL
                                                           |
                                                           v
                                            Alert Engine TODO + Forecast Service TODO
                                                           |
                                                           v
                                                    AI Agent Tools TODO
                                                           |
                                                           v
                                             React Leaflet Dashboard
                                                           |
                                                           v
                                                    HITL Approval TODO
                                                           |
                                                           v
                              FastAPI -> MQTT Command TODO -> Device Simulator TODO
```

## Components

- `simulators/sensor_simulator`: publishes PM2.5 measurements for five stations.
- `mqtt`: Eclipse Mosquitto broker with TCP and WebSocket listeners.
- `backend`: FastAPI service exposing demo REST APIs.
- `backend/db/schema.sql`: PostgreSQL schema for the future persistent system.
- `frontend`: React Leaflet dashboard with real map tiles and five markers.

## Current MVP Decision

The backend uses in-memory/mock values so the API and dashboard run immediately. Persistence from MQTT to PostgreSQL is marked as TODO for the next milestone.

## Future Work

- Add MQTT consumer service.
- Store measurements in PostgreSQL.
- Replace mock history with database queries.
- Add Open-Meteo weather collector.
- Implement baseline forecast service.
- Implement AI Agent tools and HITL approval workflow.
