
from __future__ import annotations

import json
import os
import random
import signal
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event
from typing import Any


import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL_SECONDS = int(os.getenv("SENSOR_INTERVAL_SECONDS", "10"))
MQTT_QOS = int(os.getenv("MQTT_QOS", "1"))
SCENARIO = os.getenv("SENSOR_SCENARIO", "normal")
RANDOM_SEED = os.getenv("SENSOR_RANDOM_SEED")
RUN_ID = os.getenv("SENSOR_RUN_ID") or uuid.uuid4().hex[:10]
STATION_CATALOG_PATH = Path(os.getenv("STATION_CATALOG_PATH", "/app/data/stations.json"))
VIETNAM_TZ = timezone(timedelta(hours=7))
stop_event = Event()

if RANDOM_SEED is not None:
    random.seed(int(RANDOM_SEED))


def load_stations() -> list[dict[str, Any]]:
    with STATION_CATALOG_PATH.open("r", encoding="utf-8") as file:
        stations = json.load(file)
    return [station for station in stations if station.get("station_id")]



def is_rush_hour(now: datetime) -> bool:
    return 7 <= now.hour <= 9 or 16 <= now.hour <= 18


def location_factor(location_type: str) -> float:
    factors = {
        "main_gate": 8,
        "parking": 12,
        "main_road": 15,
        "park": -8,
        "sport_area": 0,
    }
    return factors.get(location_type, 0)


def scenario_adjustment(station: dict[str, Any], counter: int, now: datetime) -> float:
    if SCENARIO == "rush-hour":
        return 18
    if SCENARIO == "spike" and station["station_id"] == "S03":
        return 45
    if SCENARIO == "recovery" and station["station_id"] == "S03":
        return max(0, 45 - counter * 3)
    if SCENARIO == "normal":
        return 12 if is_rush_hour(now) else 0
    return 0


def should_skip_station(station_id: str) -> bool:
    return SCENARIO == "station-silence" and station_id == os.getenv("SILENT_STATION_ID", "S05")


def simulate_pm25(station: dict[str, Any], counter: int, now: datetime) -> tuple[float, dict[str, float]]:
    base = float(station.get("base_pm25", 35))
    loc = location_factor(str(station.get("location_type", "")))
    wind_speed = random.uniform(0.5, 4.5)
    rainfall = random.choice([0, 0, 0, 1])
    weather_effect = -1.5 * wind_speed - (8 if rainfall else 0)
    noise = random.gauss(0, 3)
    value = base + loc + scenario_adjustment(station, counter, now) + weather_effect + noise
    weather = {
        "temperature": round(random.uniform(28, 35), 1),
        "humidity": float(random.randint(55, 85)),
        "wind_speed": round(wind_speed, 1),
        "rainfall": float(rainfall),
    }
    return round(max(1, value), 2), weather


def publish_station_status(client: mqtt.Client, station_id: str, timestamp: str, status: str = "online", reason: str | None = None) -> None:
    topic = f"airguard/stations/{station_id}/status"
    payload: dict[str, Any] = {"station_id": station_id, "status": status, "timestamp": timestamp, "source": "simulator"}
    if reason:
        payload["reason"] = reason
    client.publish(topic, json.dumps(payload, ensure_ascii=True), qos=MQTT_QOS)
    print(f"status topic={topic} station={station_id} status={status}", flush=True)


def publish_measurement(client: mqtt.Client, station: dict[str, Any], counter: int, timestamp: str, duplicate: bool = False) -> None:
    station_id = station["station_id"]
    now = datetime.fromisoformat(timestamp)
    pm25, weather = simulate_pm25(station, counter, now)
    message_counter = counter - 1 if duplicate and counter > 1 else counter
    topic = f"airguard/stations/{station_id}/measurements"
    payload = {
        "message_id": f"MSG-{RUN_ID}-{station_id}-{message_counter:06d}",
        "station_id": station_id,
        "pm25": pm25,
        "timestamp": timestamp,
        "source": "simulator",
        **weather,
    }
    client.publish(topic, json.dumps(payload, ensure_ascii=True), qos=MQTT_QOS)
    print(f"measurement topic={topic} message_id={payload['message_id']} station={station_id} pm25={pm25} scenario={SCENARIO}", flush=True)


def request_stop(signum, frame) -> None:
    print(f"Stopping simulator after signal {signum}...", flush=True)
    stop_event.set()


def main() -> None:
    if MQTT_QOS not in {0, 1, 2}:
        raise ValueError("MQTT_QOS must be 0, 1, or 2")

    stations = load_stations()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    print(f"Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT}; scenario={SCENARIO}", flush=True)

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    counter = 0
    try:
        while not stop_event.is_set():
            counter += 1
            timestamp = datetime.now(VIETNAM_TZ).isoformat()
            for station in stations:
                station_id = station["station_id"]
                if should_skip_station(station_id):
                    publish_station_status(client, station_id, timestamp, "offline", "station_silence_scenario")
                    continue
                publish_measurement(client, station, counter, timestamp)
                publish_station_status(client, station_id, timestamp)
                if SCENARIO == "duplicate" and station_id == "S03" and counter % 3 == 0:
                    publish_measurement(client, station, counter, timestamp, duplicate=True)
            stop_event.wait(INTERVAL_SECONDS)

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
