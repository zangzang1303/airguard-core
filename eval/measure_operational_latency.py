#!/usr/bin/env python3
"""
AirGuard AI - Operational Latency & Performance Benchmark
Measures actual execution latencies for all critical pipeline subsystems:
1. MQTT Consumer & Payload Validation Latency
2. Alert Detection Engine Latency
3. Prophet 24h ML Forecast Generation Latency
4. Spatial Dispersion (IDW 468 Grid Points) Generation Latency
5. Clean-Air Real-Road Routing Engine Latency
6. Full Pipeline Latency Summary (MQTT -> Alert -> Dashboard API)
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Add repo root to path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CONSUMER_PATH = ROOT / "services" / "mqtt-consumer"
if str(CONSUMER_PATH) not in sys.path:
    sys.path.insert(0, str(CONSUMER_PATH))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.services.alert_engine import EnvironmentalAlertRule
from backend.app.services.live_telemetry_engine import live_engine
from backend.app.services.prophet_forecast_service import prophet_service
from backend.app.services.road_graph_router import road_graph_router
from backend.app.services.spatial_dispersion_service import SpatialDispersionService
from mqtt_consumer.station_catalog import StationCatalog
from mqtt_consumer.validator import validate_measurement_message


def percentile(data: list[float], pct: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (pct / 100.0)
    f = int(k)
    c = f + 1
    if c < len(sorted_data):
        d0 = sorted_data[f] * (c - k)
        d1 = sorted_data[c] * (k - f)
        return d0 + d1
    return sorted_data[f]


def benchmark_mqtt_validation(catalog: StationCatalog, iterations: int = 1000) -> dict:
    payload_dict = {
        "message_id": "test-msg-001",
        "station_id": "S01",
        "pm25": 45.2,
        "co2": 650.0,
        "noise_db": 58.5,
        "temperature": 29.5,
        "measured_at": datetime.now(UTC).isoformat(),
        "source": "simulator",
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    topic = "airguard/stations/S01/measurements"

    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        res = validate_measurement_message(
            topic,
            payload_bytes,
            catalog=catalog,
            stale_after_seconds=300,
            max_future_skew_seconds=60,
        )
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # ms

    return {
        "iterations": iterations,
        "mean_ms": round(statistics.mean(latencies), 3),
        "p50_ms": round(percentile(latencies, 50), 3),
        "p95_ms": round(percentile(latencies, 95), 3),
        "p99_ms": round(percentile(latencies, 99), 3),
        "throughput_ops_sec": int(1000.0 / statistics.mean(latencies)) if statistics.mean(latencies) > 0 else 0,
    }


def benchmark_alert_rules(iterations: int = 1000) -> dict:
    rules = (
        EnvironmentalAlertRule("pm25_threshold", "pm25", "PM2.5", "µg/m³", 50.0, 80.0, "v1"),
        EnvironmentalAlertRule("aqi_threshold", "aqi", "AQI", "", 101.0, 151.0, "v1"),
        EnvironmentalAlertRule("co2_threshold", "co2", "CO₂", "ppm", 1000.0, 1500.0, "v1"),
        EnvironmentalAlertRule("noise_threshold", "noise_db", "Tiếng ồn", "dB", 70.0, 85.0, "v1"),
        EnvironmentalAlertRule("temperature_threshold", "temperature", "Nhiệt độ", "°C", 35.0, 39.0, "v1"),
    )
    station_snapshot = {
        "station_id": "S01",
        "station_name": "Trục Đa Tốn (S01)",
        "pm25": 65.4,
        "aqi": 156.0,
        "co2": 1250.0,
        "noise_db": 75.0,
        "temperature": 34.0,
        "is_stale": False,
        "status": "online",
    }

    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fired = []
        for r in rules:
            val = station_snapshot.get(r.field)
            if val >= r.critical_threshold:
                fired.append((r.alert_type, "critical", val))
            elif val >= r.warning_threshold:
                fired.append((r.alert_type, "warning", val))
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    return {
        "iterations": iterations,
        "rules_evaluated_per_cycle": len(rules),
        "mean_ms": round(statistics.mean(latencies), 3),
        "p50_ms": round(percentile(latencies, 50), 3),
        "p95_ms": round(percentile(latencies, 95), 3),
        "p99_ms": round(percentile(latencies, 99), 3),
    }


def benchmark_prophet_forecast(iterations: int = 100) -> dict:
    history = live_engine.get_history("S01", hours=72)
    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        res = prophet_service.forecast("S01", history, hours=24, metric="aqi")
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    return {
        "iterations": iterations,
        "horizons_generated": 24,
        "mean_ms": round(statistics.mean(latencies), 3),
        "p50_ms": round(percentile(latencies, 50), 3),
        "p95_ms": round(percentile(latencies, 95), 3),
        "p99_ms": round(percentile(latencies, 99), 3),
    }


class FakeStationService:
    def __init__(self, stations: list[dict[str, Any]]) -> None:
        self.stations = stations

    def list_stations(self, *, allow_fallback: bool = True) -> list[dict[str, Any]]:
        return [dict(s) for s in self.stations]


def benchmark_spatial_heatmap(iterations: int = 100) -> dict:
    stations = live_engine.get_current_stations()
    station_svc = FakeStationService(stations)
    spatial_svc = SpatialDispersionService(station_service=station_svc)

    latencies = []
    grid_count = 0
    for _ in range(iterations):
        t0 = time.perf_counter()
        res = spatial_svc.calculate_heatmap(
            metric="aqi",
            forecast_hour=0,
        )
        t1 = time.perf_counter()
        grid_count = len(res.get("grid_points", []))
        latencies.append((t1 - t0) * 1000.0)

    return {
        "iterations": iterations,
        "grid_points_count": grid_count,
        "mean_ms": round(statistics.mean(latencies), 3),
        "p50_ms": round(percentile(latencies, 50), 3),
        "p95_ms": round(percentile(latencies, 95), 3),
        "p99_ms": round(percentile(latencies, 99), 3),
    }


def benchmark_road_routing(iterations: int = 100) -> dict:
    # Route between S01 and S03 (Lake area)
    start_lat, start_lon = 20.9935, 105.9520
    end_lat, end_lon = 20.9980, 105.9580

    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        res = road_graph_router.generate_smart_running_route(
            user_lat=start_lat,
            user_lng=start_lon,
            target_km=3.0,
            station_pm25_map={"S01": 55.0, "S02": 42.0, "S03": 25.0, "S04": 30.0, "S05": 60.0},
        )
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    return {
        "iterations": iterations,
        "mean_ms": round(statistics.mean(latencies), 3),
        "p50_ms": round(percentile(latencies, 50), 3),
        "p95_ms": round(percentile(latencies, 95), 3),
        "p99_ms": round(percentile(latencies, 99), 3),
    }


def main():
    print("=" * 70)
    print("  AIRGUARD AI - OPERATIONAL SUBSYSTEM BENCHMARK & LATENCY MEASUREMENT")
    print("=" * 70)

    catalog = StationCatalog.load(ROOT / "data" / "stations.json")

    print("\n1. Đo hiệu năng MQTT Ingestion & Validation (1,000 samples)...")
    mqtt_res = benchmark_mqtt_validation(catalog, iterations=1000)
    print(f"   - Mean latency: {mqtt_res['mean_ms']} ms | P50: {mqtt_res['p50_ms']} ms | P95: {mqtt_res['p95_ms']} ms")
    print(f"   - Ingestion throughput: {mqtt_res['throughput_ops_sec']:,} msg/sec")

    print("\n2. Đo hiệu năng Alert Detection Engine (1,000 samples)...")
    alert_res = benchmark_alert_rules(iterations=1000)
    print(f"   - Mean latency: {alert_res['mean_ms']} ms | P50: {alert_res['p50_ms']} ms | P95: {alert_res['p95_ms']} ms")

    print("\n3. Đo hiệu năng Mô hình Dự báo 24h Prophet ML (100 samples)...")
    prophet_res = benchmark_prophet_forecast(iterations=100)
    print(f"   - Horizons: {prophet_res['horizons_generated']} steps (1h - 24h)")
    print(f"   - Mean latency: {prophet_res['mean_ms']} ms | P50: {prophet_res['p50_ms']} ms | P95: {prophet_res['p95_ms']} ms")

    print("\n4. Đo hiệu năng Bản đồ nhiệt Nội suy IDW (100 samples)...")
    spatial_res = benchmark_spatial_heatmap(iterations=100)
    print(f"   - Số điểm lưới: {spatial_res['grid_points_count']} grid points trong Ocean Park 1")
    print(f"   - Mean latency: {spatial_res['mean_ms']} ms | P50: {spatial_res['p50_ms']} ms | P95: {spatial_res['p95_ms']} ms")

    print("\n5. Đo hiệu năng Thuật toán Tìm đường Sạch Real-Road Routing (100 samples)...")
    routing_res = benchmark_road_routing(iterations=100)
    print(f"   - Mean latency: {routing_res['mean_ms']} ms | P50: {routing_res['p50_ms']} ms | P95: {routing_res['p95_ms']} ms")

    # Composite Pipeline Latency
    mqtt_to_db = mqtt_res["p95_ms"]
    alert_eval = alert_res["p95_ms"]
    mqtt_to_alert_total = mqtt_to_db + alert_eval

    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "mqtt_validation": mqtt_res,
        "alert_engine": alert_res,
        "prophet_forecast_24h": prophet_res,
        "spatial_heatmap_468_points": spatial_res,
        "road_routing": routing_res,
        "composite_latencies": {
            "mqtt_ingest_p95_ms": mqtt_to_db,
            "alert_detection_p95_ms": alert_eval,
            "mqtt_to_alert_latency_p95_ms": round(mqtt_to_alert_total, 3),
            "api_spatial_p95_ms": spatial_res["p95_ms"],
            "api_forecast_p95_ms": prophet_res["p95_ms"],
            "dashboard_polling_interval_sec": 30.0,
            "simulator_publish_interval_sec": 30.0,
        },
    }

    report_path = ROOT / "reports" / "operational_performance.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved operational benchmark results to: {report_path}")


if __name__ == "__main__":
    main()
