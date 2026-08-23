from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from fastapi.testclient import TestClient

from app.main import app
from app.services.alert_engine import AlertEngine
from app.services.audit_service import AuditService
from app.services.database import Database
from app.services.live_telemetry_engine import LiveTelemetryEngine
from app.services.spatial_registry import SpatialRegistry
from app.services.station_service import StationService


CANONICAL_STATIONS = {
    "S01": {
        "station_name": "Trục Đa Tốn phía Tây Bắc",
        "description": "Điểm mô phỏng trên trục Đa Tốn, phủ khu vực cửa ngõ Tây Bắc Ocean Park 1",
    },
    "S02": {
        "station_name": "Khu căn hộ Sapphire",
        "description": "Điểm mô phỏng trong cụm căn hộ phía Tây Bắc, đại diện khu dân cư mật độ cao",
    },
    "S03": {
        "station_name": "Ven Hồ Ngọc Trai",
        "description": "Điểm mô phỏng ven Hồ Ngọc Trai và khu Ngọc Trai, đại diện không gian ven hồ trung tâm",
    },
    "S04": {
        "station_name": "Khuôn viên VinUni",
        "description": "Điểm mô phỏng trong khuôn viên VinUni ở phía Tây Nam phạm vi quan sát",
    },
    "S05": {
        "station_name": "Khu Hải Âu phía Đông Nam",
        "description": "Điểm mô phỏng tại khu Hải Âu, phủ vùng dân cư phía Đông Nam Ocean Park 1",
    },
}


def test_stations_json_has_exact_canonical_utf8_names():
    root = Path(__file__).resolve().parent.parent.parent
    stations_path = root / "data" / "stations.json"
    assert stations_path.exists(), "data/stations.json must exist"

    with stations_path.open("r", encoding="utf-8") as f:
        stations = json.load(f)

    station_dict = {item["station_id"]: item for item in stations}
    for st_id, expected in CANONICAL_STATIONS.items():
        assert st_id in station_dict, f"Station {st_id} missing in data/stations.json"
        actual_name = station_dict[st_id]["station_name"]
        assert actual_name == expected["station_name"], f"Mismatch for {st_id}: {actual_name} != {expected['station_name']}"
        assert "?" not in actual_name, f"Broken character '?' found in {actual_name}"
        assert "\ufffd" not in actual_name, f"Unicode replacement character found in {actual_name}"


def test_schema_and_seed_sql_have_exact_canonical_utf8_names():
    root = Path(__file__).resolve().parent.parent.parent
    schema_path = root / "backend" / "db" / "schema.sql"
    seed_path = root / "backend" / "db" / "seed.sql"

    for sql_path in (schema_path, seed_path):
        assert sql_path.exists(), f"{sql_path} must exist"
        content = sql_path.read_text(encoding="utf-8")
        for st_id, expected in CANONICAL_STATIONS.items():
            assert expected["station_name"] in content, f"{sql_path.name} missing '{expected['station_name']}'"
            assert expected["description"] in content, f"{sql_path.name} missing '{expected['description']}'"


def test_live_engine_and_spatial_registry_have_canonical_names():
    engine = LiveTelemetryEngine()
    for defn in engine.STATION_DEFINITIONS:
        st_id = defn["station_id"]
        assert defn["station_name"] == CANONICAL_STATIONS[st_id]["station_name"]
        assert "?" not in defn["station_name"]

    for st_id, expected in CANONICAL_STATIONS.items():
        assert st_id in SpatialRegistry.STATIONS
        assert SpatialRegistry.STATIONS[st_id]["name"] == expected["station_name"]


def test_station_service_fallback_returns_canonical_names():
    db = Database(None)
    station_service = StationService(db, stale_after_seconds=300)
    stations = station_service.list_stations(allow_fallback=True)

    station_dict = {s["station_id"]: s for s in stations}
    for st_id, expected in CANONICAL_STATIONS.items():
        assert st_id in station_dict
        assert station_dict[st_id]["station_name"] == expected["station_name"]
        assert "?" not in station_dict[st_id]["station_name"]
        assert "\ufffd" not in station_dict[st_id]["station_name"]


def test_api_stations_returns_canonical_vietnamese_names():
    client = TestClient(app)
    response = client.get("/api/v1/stations")
    assert response.status_code == 200
    data = response.json()
    items = {item["station_id"]: item for item in data["items"]}

    assert items["S05"]["station_name"] == "Khu Hải Âu phía Đông Nam"
    assert items["S02"]["station_name"] == "Khu căn hộ Sapphire"
    assert items["S01"]["station_name"] == "Trục Đa Tốn phía Tây Bắc"
    assert items["S03"]["station_name"] == "Ven Hồ Ngọc Trai"
    assert items["S04"]["station_name"] == "Khuôn viên VinUni"

    for item in items.values():
        name = item["station_name"]
        assert "?" not in name, f"Broken character '?' in station_name {name}"
        assert "\ufffd" not in name, f"Replacement character in station_name {name}"


def test_alert_engine_generates_correct_vietnamese_titles():
    db = Database(None)
    station_service = StationService(db, stale_after_seconds=300)
    audit = AuditService(db)

    engine = AlertEngine(
        db,
        station_service,
        audit,
        warning_threshold=35.0,
        critical_threshold=75.0,
        rule_version="pm25-threshold-v1",
    )

    # Test title formatting for all 5 stations
    for st_id, expected in CANONICAL_STATIONS.items():
        station_snapshot = {
            "station_id": st_id,
            "station_name": expected["station_name"],
            "pm25": 60.0,
            "is_stale": False,
            "status": "online",
        }
        for rule in engine.rules:
            title = f"{rule.label} vượt ngưỡng tại {station_snapshot['station_name']}"
            assert expected["station_name"] in title
            assert "?" not in title
            assert "\ufffd" not in title

    # Explicit acceptance criteria check:
    title_s05 = f"PM2.5 vượt ngưỡng tại {CANONICAL_STATIONS['S05']['station_name']}"
    assert title_s05 == "PM2.5 vượt ngưỡng tại Khu Hải Âu phía Đông Nam"


def test_migration_003_sql_structure_and_safety():
    root = Path(__file__).resolve().parent.parent.parent
    migration_path = root / "backend" / "db" / "migrations" / "20260823_003_fix_vietnamese_station_names_and_alerts.sql"
    assert migration_path.exists(), "Migration 003 must exist"

    sql = migration_path.read_text(encoding="utf-8")
    assert "BEGIN;" in sql
    assert "COMMIT;" in sql
    assert "ON CONFLICT (station_id) DO UPDATE SET" in sql
    assert "Trục Đa Tốn phía Tây Bắc" in sql
    assert "Khu căn hộ Sapphire" in sql
    assert "Ven Hồ Ngọc Trai" in sql
    assert "Khuôn viên VinUni" in sql
    assert "Khu Hải Âu phía Đông Nam" in sql
    assert "UPDATE alerts" in sql
    assert "regexp_replace(alerts.description" in sql


def test_compose_and_local_bootstrap_apply_migration_003():
    root = Path(__file__).resolve().parent.parent.parent
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    init_script = (root / "scripts" / "init-demo-db.ps1").read_text(encoding="utf-8")
    migration_path = "/migrations/20260823_003_fix_vietnamese_station_names_and_alerts.sql"

    assert migration_path in compose
    assert migration_path in init_script
    assert re.search(
        r"postgres:\s+.*?\./backend/db/migrations:/migrations:ro",
        compose,
        flags=re.DOTALL,
    )


CANONICAL_DEMO_USERS = {
    "manager@vinuni.edu.vn": "Nguyễn Văn A",
    "admin@vinuni.edu.vn": "Lê Thị D",
    "resident@vinuni.edu.vn": "Trần Minh Anh",
}


def test_migration_004_sql_structure_and_safety():
    root = Path(__file__).resolve().parent.parent.parent
    migration_path = root / "backend" / "db" / "migrations" / "20260823_004_fix_vietnamese_demo_user_names.sql"
    assert migration_path.exists(), "Migration 004 must exist"

    sql = migration_path.read_text(encoding="utf-8")
    assert "BEGIN;" in sql
    assert "COMMIT;" in sql
    assert "UPDATE users" in sql
    assert "IS DISTINCT FROM" in sql
    assert "LOWER(BTRIM(u.email))" in sql or "email_normalized" in sql

    for email, full_name in CANONICAL_DEMO_USERS.items():
        assert email in sql, f"Migration 004 missing email '{email}'"
        assert full_name in sql, f"Migration 004 missing full_name '{full_name}'"
        assert "?" not in full_name
        assert "\ufffd" not in full_name

    # Safety checks: must not contain destructive operations or unauthorized inserts
    assert "DELETE" not in sql
    assert "TRUNCATE" not in sql
    assert "INSERT INTO users" not in sql
    assert "DROP TABLE" not in sql


def test_compose_and_local_bootstrap_apply_migration_004():
    root = Path(__file__).resolve().parent.parent.parent
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    init_script = (root / "scripts" / "init-demo-db.ps1").read_text(encoding="utf-8")
    mig_003 = "20260823_003_fix_vietnamese_station_names_and_alerts.sql"
    mig_004 = "20260823_004_fix_vietnamese_demo_user_names.sql"

    assert f"/migrations/{mig_004}" in compose
    assert f"/migrations/{mig_004}" in init_script

    # Verify migration 004 is executed AFTER migration 003
    pos_003_compose = compose.find(mig_003)
    pos_004_compose = compose.find(mig_004)
    assert pos_003_compose != -1 and pos_004_compose != -1
    assert pos_004_compose > pos_003_compose, "Migration 004 must come after 003 in docker-compose.yml"

    pos_003_init = init_script.find(mig_003)
    pos_004_init = init_script.find(mig_004)
    assert pos_003_init != -1 and pos_004_init != -1
    assert pos_004_init > pos_003_init, "Migration 004 must come after 003 in init-demo-db.ps1"


def test_demo_users_seed_has_canonical_utf8_names():
    root = Path(__file__).resolve().parent.parent.parent
    seed_path = root / "backend" / "db" / "seed.sql"
    content = seed_path.read_text(encoding="utf-8")

    for email, expected_name in CANONICAL_DEMO_USERS.items():
        assert email in content
        assert expected_name in content

