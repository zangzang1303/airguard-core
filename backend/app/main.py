from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.services.agent_service import build_placeholder_answer
from app.services.forecast_service import baseline_forecast

VIETNAM_TZ = timezone(timedelta(hours=7))
DATA_PATHS = [Path("/app/data/stations.json"), Path(__file__).resolve().parents[2] / "data" / "stations.json"]


class AgentChatRequest(BaseModel):
    user_id: str = Field(..., examples=["demo-user"])
    message: str = Field(..., examples=["Hien tai co nen chay bo o cong vien khong?"])


def load_stations() -> list[dict]:
    for path in DATA_PATHS:
        if path.exists():
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
    return []


def pm25_level(pm25: float) -> str:
    if pm25 <= 25:
        return "good"
    if pm25 <= 50:
        return "moderate"
    if pm25 <= 100:
        return "unhealthy"
    return "very_unhealthy"


def current_pm25(station: dict) -> float:
    location_adjustment = {
        "main_gate": 4.5,
        "parking": 9.0,
        "main_road": 12.0,
        "park": -5.0,
        "sport_area": 1.5,
    }.get(station["location_type"], 0.0)
    return round(max(1.0, station["base_pm25"] + location_adjustment), 2)


def station_response(station: dict) -> dict:
    pm25 = current_pm25(station)
    return {
        **station,
        "pm25": pm25,
        "status": "online",
        "level": pm25_level(pm25),
        "updated_at": datetime.now(VIETNAM_TZ).isoformat(),
        "source": "simulator_mock",
    }


def get_station_or_404(station_id: str) -> dict:
    for station in load_stations():
        if station["station_id"] == station_id:
            return station
    raise HTTPException(status_code=404, detail="station_not_found")


app = FastAPI(title="AirGuard AI API", version="0.1.0")

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "airguard-api", "version": "0.1.0"}


@app.get("/api/v1/stations")
def get_stations() -> dict:
    return {"items": [station_response(station) for station in load_stations()]}


@app.get("/api/v1/stations/{station_id}")
def get_station(station_id: str) -> dict:
    return station_response(get_station_or_404(station_id))


@app.get("/api/v1/stations/{station_id}/current")
def get_station_current(station_id: str) -> dict:
    return station_response(get_station_or_404(station_id))


@app.get("/api/v1/stations/{station_id}/history")
def get_station_history(station_id: str, hours: int = Query(default=24, ge=1, le=72)) -> dict:
    station = get_station_or_404(station_id)
    base = current_pm25(station)
    now = datetime.now(VIETNAM_TZ).replace(minute=0, second=0, microsecond=0)
    points = []
    for offset in range(hours):
        measured_at = now - timedelta(hours=hours - offset - 1)
        daily_wave = ((offset % 6) - 2) * 1.8
        points.append(
            {
                "station_id": station_id,
                "measured_at": measured_at.isoformat(),
                "pm25": round(max(1.0, base + daily_wave), 2),
                "source": "simulator_mock",
            }
        )
    return {"station_id": station_id, "hours": hours, "items": points}


@app.get("/api/v1/alerts")
def get_alerts() -> dict:
    alerts = []
    for station in load_stations():
        current = station_response(station)
        if current["pm25"] > 50:
            alerts.append(
                {
                    "alert_id": str(uuid4()),
                    "station_id": current["station_id"],
                    "alert_type": "pm25_threshold",
                    "severity": "warning" if current["pm25"] <= 100 else "critical",
                    "observed_value": current["pm25"],
                    "threshold_value": 50,
                    "title": f"PM2.5 elevated at {current['station_name']}",
                    "description": "Mock alert generated from current simulator baseline.",
                    "status": "active",
                    "created_at": current["updated_at"],
                }
            )
    return {"items": alerts}


@app.post("/api/v1/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str) -> dict:
    return {"alert_id": alert_id, "status": "resolved", "todo": "Persist alert status in PostgreSQL."}


@app.get("/api/v1/weather/current")
def get_current_weather() -> dict:
    return {
        "area_id": "vinuni-ocean-park",
        "temperature": 31.5,
        "humidity": 72,
        "wind_speed": 2.4,
        "rainfall": 0,
        "source": "mock_weather_context",
        "todo": "Replace with Open-Meteo collector.",
        "observed_at": datetime.now(VIETNAM_TZ).isoformat(),
    }


@app.get("/api/v1/stations/{station_id}/forecast")
def get_station_forecast(station_id: str, hours: int = Query(default=3, ge=1, le=3)) -> dict:
    station = station_response(get_station_or_404(station_id))
    return {
        "station_id": station_id,
        "items": baseline_forecast(station["pm25"], hours),
        "todo": "Replace placeholder with moving average or regression forecast.",
    }


@app.post("/api/v1/agent/chat")
def agent_chat(request: AgentChatRequest) -> dict:
    return {"user_id": request.user_id, **build_placeholder_answer(request.message)}


@app.get("/api/v1/approvals")
def get_approvals() -> dict:
    return {"items": [], "todo": "Implement HITL approval persistence and review actions."}


@app.post("/api/v1/approvals/{request_id}/approve")
def approve_request(request_id: str) -> dict:
    return {"request_id": request_id, "status": "approved", "todo": "Publish MQTT command only after approval."}


@app.post("/api/v1/approvals/{request_id}/reject")
def reject_request(request_id: str) -> dict:
    return {"request_id": request_id, "status": "rejected", "todo": "Persist reviewer note and audit log."}


@app.get("/api/v1/devices")
def get_devices() -> dict:
    return {
        "items": [
            {
                "device_id": "FILTER-01",
                "device_name": "Simulated outdoor filtration unit",
                "device_type": "air_filter",
                "station_id": "S03",
                "status": "offline",
                "is_simulated": True,
            }
        ]
    }


@app.get("/api/v1/devices/{device_id}/status")
def get_device_status(device_id: str) -> dict:
    if device_id != "FILTER-01":
        raise HTTPException(status_code=404, detail="device_not_found")
    return {"device_id": device_id, "status": "offline", "is_simulated": True}
