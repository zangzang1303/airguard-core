from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .audit_service import AuditService
from .database import Database, ServiceError, dict_cursor
from .station_service import StationService


@dataclass(frozen=True)
class EnvironmentalAlertRule:
    alert_type: str
    field: str
    label: str
    unit: str
    warning_threshold: float
    critical_threshold: float
    rule_version: str


class AlertEngine:
    """Creates deduplicated deterministic alerts from fresh station snapshots only."""

    def __init__(
        self,
        db: Database,
        station_service: StationService,
        audit: AuditService,
        *,
        warning_threshold: float,
        critical_threshold: float,
        rule_version: str,
        consecutive_measurements: int = 1,
        stale_after_seconds: int = 300,
        aqi_warning_threshold: float = 101,
        aqi_critical_threshold: float = 151,
        co2_warning_threshold: float = 1000,
        co2_critical_threshold: float = 1500,
        noise_warning_threshold: float = 70,
        noise_critical_threshold: float = 85,
        temperature_warning_threshold: float = 35,
        temperature_critical_threshold: float = 39,
        environmental_rule_version: str = "environmental-threshold-v1",
    ) -> None:
        self.db = db
        self.station_service = station_service
        self.audit = audit
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.rule_version = rule_version
        self.consecutive_measurements = max(1, consecutive_measurements)
        self.stale_after_seconds = max(1, stale_after_seconds)
        self.rules = (
            EnvironmentalAlertRule("pm25_threshold", "pm25", "PM2.5", "µg/m³", warning_threshold, critical_threshold, rule_version),
            EnvironmentalAlertRule("aqi_threshold", "aqi", "AQI", "", aqi_warning_threshold, aqi_critical_threshold, environmental_rule_version),
            EnvironmentalAlertRule("co2_threshold", "co2", "CO₂", "ppm", co2_warning_threshold, co2_critical_threshold, environmental_rule_version),
            EnvironmentalAlertRule("noise_threshold", "noise_db", "Tiếng ồn", "dB", noise_warning_threshold, noise_critical_threshold, environmental_rule_version),
            EnvironmentalAlertRule("temperature_threshold", "temperature", "Nhiệt độ", "°C", temperature_warning_threshold, temperature_critical_threshold, environmental_rule_version),
        )

    def evaluate_all_current(self, correlation_id: str | None = None) -> None:
        for station in self.station_service.list_stations():
            self.evaluate_station(station["station_id"], correlation_id=correlation_id)

    def evaluate_station(self, station_id: str, correlation_id: str | None = None) -> dict[str, Any] | None:
        station = self.station_service.get_station(station_id)
        unavailable = station["is_stale"] or station["status"] in {"offline", "stale"} or station["pm25"] is None
        if unavailable:
            return self._evaluate_sensor_offline(station, correlation_id=correlation_id)

        self._resolve_sensor_offline(station_id, correlation_id=correlation_id)
        evaluated = [
            alert for rule in self.rules
            if (alert := self._evaluate_rule(station, rule, correlation_id=correlation_id)) is not None
        ]
        return max(evaluated, key=lambda item: (self._severity_rank(item["severity"]), item["updated_at"])) if evaluated else None

    def _evaluate_rule(
        self,
        station: dict[str, Any],
        rule: EnvironmentalAlertRule,
        *,
        correlation_id: str | None,
    ) -> dict[str, Any] | None:
        raw_value = station.get(rule.field)
        if raw_value is None:
            return None
        value = float(raw_value)
        severity = self._severity_for(value, rule)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT * FROM alerts
                    WHERE station_id = %s AND alert_type = %s AND rule_version = %s AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (station["station_id"], rule.alert_type, rule.rule_version),
                )
                existing = cur.fetchone()

                if severity is None:
                    return self._resolve_rule_alert(cur, existing, station, rule, value, correlation_id, conn)

                if rule.field == "pm25" and not self._pm25_threshold_is_qualified(station["station_id"]):
                    return dict(existing) if existing else None

                recommendation = self._recommendation(rule, severity)
                title = f"{rule.label} vượt ngưỡng tại {station['station_name']}"
                description = (
                    f"Dữ liệu simulator hợp lệ, mới nhất: {rule.label} {value:g}{(' ' + rule.unit) if rule.unit else ''}; "
                    f"ngưỡng cảnh báo {rule.warning_threshold:g}{(' ' + rule.unit) if rule.unit else ''}. "
                    f"Khuyến nghị: {recommendation}"
                )
                if existing:
                    cur.execute(
                        """
                        UPDATE alerts SET severity = %s, observed_value = %s, threshold_value = %s,
                            title = %s, description = %s, updated_at = NOW()
                        WHERE alert_id = %s RETURNING *
                        """,
                        (severity, value, rule.warning_threshold, title, description, existing["alert_id"]),
                    )
                    return dict(cur.fetchone())

                cur.execute(
                    """
                    INSERT INTO alerts (alert_id, station_id, alert_type, rule_version, severity,
                        observed_value, threshold_value, title, description, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active') RETURNING *
                    """,
                    (str(uuid4()), station["station_id"], rule.alert_type, rule.rule_version, severity,
                     value, rule.warning_threshold, title, description),
                )
                created = dict(cur.fetchone())
                self.audit.record(
                    actor_type="system", actor_role="backend", action="alert.create", entity_type="alert",
                    entity_id=str(created["alert_id"]), correlation_id=correlation_id,
                    details={"station_id": station["station_id"], "alert_type": rule.alert_type,
                             "observed_value": value, "threshold": rule.warning_threshold}, conn=conn,
                )
                return created

    def _resolve_rule_alert(self, cur: Any, existing: Any, station: dict[str, Any], rule: EnvironmentalAlertRule,
                            value: float, correlation_id: str | None, conn: Any) -> dict[str, Any] | None:
        if not existing:
            return None
        cur.execute(
            """UPDATE alerts SET status = 'resolved', resolved_at = NOW(), updated_at = NOW(),
               description = COALESCE(description, '') || ' Tự động đóng: chỉ số đã về dưới ngưỡng.'
               WHERE alert_id = %s RETURNING *""",
            (existing["alert_id"],),
        )
        resolved = dict(cur.fetchone())
        self.audit.record(
            actor_type="system", actor_role="backend", action="alert.auto_resolve", entity_type="alert",
            entity_id=str(resolved["alert_id"]), correlation_id=correlation_id,
            details={"station_id": station["station_id"], "alert_type": rule.alert_type, "observed_value": value}, conn=conn,
        )
        return resolved

    def _pm25_threshold_is_qualified(self, station_id: str) -> bool:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """SELECT pm25 FROM measurements WHERE station_id = %s AND quality_flag = 'valid'
                       AND measured_at >= NOW() - (%s * INTERVAL '1 second')
                       ORDER BY measured_at DESC LIMIT %s""",
                    (station_id, self.stale_after_seconds, self.consecutive_measurements),
                )
                values = [float(row["pm25"]) for row in cur.fetchall()]
        return self._threshold_is_qualified(values)

    def _evaluate_sensor_offline(self, station: dict[str, Any], *, correlation_id: str | None) -> dict[str, Any] | None:
        has_seen = station.get("last_seen_at") is not None or station.get("updated_at") is not None
        if not has_seen:
            return None
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute("""SELECT * FROM alerts WHERE station_id = %s AND alert_type = 'sensor_offline'
                    AND rule_version = %s AND status = 'active' ORDER BY created_at DESC LIMIT 1""",
                    (station["station_id"], self.rule_version))
                existing = cur.fetchone()
                if existing:
                    return dict(existing)
                cur.execute("""INSERT INTO alerts (alert_id, station_id, alert_type, rule_version, severity, title, description, status)
                    VALUES (%s, %s, 'sensor_offline', %s, 'warning', %s, %s, 'active') RETURNING *""",
                    (str(uuid4()), station["station_id"], self.rule_version,
                     f"Sensor unavailable at {station['station_name']}", "No valid fresh measurement is available for this station."))
                created = dict(cur.fetchone())
                self.audit.record(actor_type="system", actor_role="backend", action="alert.sensor_offline", entity_type="alert",
                                  entity_id=str(created["alert_id"]), correlation_id=correlation_id,
                                  details={"station_id": station["station_id"], "status": station.get("status")}, conn=conn)
                return created

    def _resolve_sensor_offline(self, station_id: str, *, correlation_id: str | None) -> None:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute("""UPDATE alerts SET status = 'resolved', resolved_at = NOW(), updated_at = NOW()
                    WHERE station_id = %s AND alert_type = 'sensor_offline' AND rule_version = %s AND status = 'active'
                    RETURNING alert_id""", (station_id, self.rule_version))
                row = cur.fetchone()
                if row:
                    self.audit.record(actor_type="system", actor_role="backend", action="alert.sensor_recovered", entity_type="alert",
                                      entity_id=str(row["alert_id"]), correlation_id=correlation_id,
                                      details={"station_id": station_id}, conn=conn)

    @staticmethod
    def _severity_for(value: float, rule: EnvironmentalAlertRule) -> str | None:
        if value >= rule.critical_threshold:
            return "critical"
        if value >= rule.warning_threshold:
            return "warning"
        return None

    def _threshold_is_qualified(self, values: list[float]) -> bool:
        return len(values) >= self.consecutive_measurements and all(
            value >= self.warning_threshold for value in values[:self.consecutive_measurements]
        )

    @staticmethod
    def _severity_rank(severity: str) -> int:
        return {"critical": 2, "warning": 1}.get(severity, 0)

    @staticmethod
    def _recommendation(rule: EnvironmentalAlertRule, severity: str) -> str:
        if rule.alert_type == "aqi_threshold":
            return "Giảm hoạt động ngoài trời kéo dài; nhóm nhạy cảm nên ưu tiên theo dõi cập nhật AQI."
        if rule.alert_type == "pm25_threshold":
            return "Hạn chế nguồn bụi gần khu vực và theo dõi lần đo kế tiếp trước khi thực hiện hành động cần phê duyệt."
        if rule.alert_type == "co2_threshold":
            return "Kiểm tra thông gió tại khu vực trong nhà hoặc đông người; không dùng cảnh báo này để chẩn đoán sức khỏe."
        if rule.alert_type == "noise_threshold":
            return "Kiểm tra hoạt động gây ồn và cân nhắc giảm nguồn ồn theo quy trình vận hành."
        if rule.alert_type == "temperature_threshold":
            return "Bố trí nghỉ, nước uống và theo dõi điều kiện thời tiết cho hoạt động ngoài trời."
        return "Theo dõi dữ liệu tại trạm và thực hiện theo quy trình vận hành."

    @staticmethod
    def _with_source(alert: dict[str, Any]) -> dict[str, Any]:
        return {**alert, "source": f"backend_alert_rule:{alert['rule_version']}"}

    def list_alerts(self, *, status: str | None = None, station_id: str | None = None) -> list[dict[str, Any]]:
        self.evaluate_all_current()
        clauses, params = [], []
        if status:
            clauses.append("status = %s"); params.append(status)
        if station_id:
            clauses.append("station_id = %s"); params.append(station_id)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(f"""SELECT alert_id, station_id, alert_type, rule_version, severity, observed_value,
                    threshold_value, title, description, status, created_at, updated_at, resolved_at FROM alerts {where}
                    ORDER BY created_at DESC""", params)
                return [self._enrich_alert(dict(row)) for row in cur.fetchall()]

    def _enrich_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        rule = next((item for item in self.rules if item.alert_type == alert.get("alert_type")), None)
        enriched = self._with_source(alert)
        if rule is None:
            return enriched
        return {
            **enriched,
            "metric": rule.label,
            "unit": rule.unit,
            "recommendation": self._recommendation(rule, str(alert.get("severity") or "warning")),
        }

    def resolve_alert(self, alert_id: str, *, actor_id: str, actor_role: str, correlation_id: str | None) -> dict[str, Any]:
        if actor_role != "manager":
            raise ServiceError("forbidden", "Only manager role can resolve alerts", 403)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute("""UPDATE alerts SET status = 'resolved', resolved_at = COALESCE(resolved_at, NOW()), updated_at = NOW()
                    WHERE alert_id = %s AND status = 'active' RETURNING *""", (alert_id,))
                row = cur.fetchone()
                if not row:
                    raise ServiceError("alert_not_found_or_not_active", "Alert was not found or is not active", 404)
                alert = dict(row)
                self.audit.record(actor_type="user", actor_id=actor_id, actor_role=actor_role, action="alert.manual_resolve",
                                  entity_type="alert", entity_id=str(alert_id), correlation_id=correlation_id,
                                  details={"station_id": alert.get("station_id"), "alert_type": alert.get("alert_type")}, conn=conn)
                return alert
