import json
import os
import random
import time
from datetime import datetime, timedelta, timezone

import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL_SECONDS = int(os.getenv("SENSOR_INTERVAL_SECONDS", "10"))

VIETNAM_TZ = timezone(timedelta(hours=7))

STATIONS = [
    {"station_id": "S01", "station_name": "Cong chinh", "location_type": "main_gate", "base_pm25": 38},
    {"station_id": "S02", "station_name": "Bai do xe", "location_type": "parking", "base_pm25": 42},
    {"station_id": "S03", "station_name": "Truc duong chinh", "location_type": "main_road", "base_pm25": 45},
    {"station_id": "S04", "station_name": "Cong vien", "location_type": "park", "base_pm25": 28},
    {"station_id": "S05", "station_name": "Khu the thao ngoai troi", "location_type": "sport_area", "base_pm25": 34},
]


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


def simulate_pm25(station: dict) -> float:
    now = datetime.now(VIETNAM_TZ)
    base = station["base_pm25"]
    rush = 12 if is_rush_hour(now) else 0
    loc = location_factor(station["location_type"])
    wind_speed = random.uniform(0.5, 4.5)
    rainfall = random.choice([0, 0, 0, 1])
    weather_effect = -1.5 * wind_speed - (8 if rainfall else 0)
    noise = random.gauss(0, 3)
    value = base + rush + loc + weather_effect + noise
    return round(max(1, value), 2)


def publish_station_status(client: mqtt.Client, station: dict, timestamp: str) -> None:
    topic = f"airguard/stations/{station['station_id']}/status"
    payload = {"station_id": station["station_id"], "status": "online", "timestamp": timestamp}
    client.publish(topic, json.dumps(payload), qos=0)


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    print(f"Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT}", flush=True)

    counter = 0
    try:
        while True:
            counter += 1
            now = datetime.now(VIETNAM_TZ).isoformat()
            for station in STATIONS:
                pm25 = simulate_pm25(station)
                topic = f"airguard/stations/{station['station_id']}/measurements"
                payload = {
                    "message_id": f"MSG-{station['station_id']}-{counter}",
                    "station_id": station["station_id"],
                    "pm25": pm25,
                    "temperature": round(random.uniform(28, 35), 1),
                    "humidity": random.randint(55, 85),
                    "wind_speed": round(random.uniform(0.5, 4.5), 1),
                    "rainfall": random.choice([0, 0, 0, 1]),
                    "timestamp": now,
                    "source": "simulator",
                }
                client.publish(topic, json.dumps(payload), qos=0)
                publish_station_status(client, station, now)
                print(topic, payload, flush=True)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Stopping simulator...", flush=True)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
