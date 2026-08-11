from __future__ import annotations

from typing import Any
from uuid import uuid4

from .audit_service import AuditService
from .database import Database, ServiceError, dict_cursor
from .station_service import StationService


class AlertEngine:
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
    ) -> None:
        self.db = db
        self.station_service = station_service
        self.audit = audit
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.rule_version = rule_version
        self.consecutive_measurements = max(1, consecutive_measurements)
        self.stale_after_seconds = max(1, stale_after_seconds)

    def evaluate_all_current(self, correlation_id: str | None = None) -> None:
        for station in self.station_service.list_stations():
            self.evaluate_station(station["station_id"], correlation_id=correlation_id)

    def evaluate_station(self, station_id: str, correlation_id: str | None = None) -> dict[str, Any] | None:
        station = self.station_service.get_station(station_id)
        unavailable = station["is_stale"] or station["status"] in {"offline", "stale"} or station["pm25"] is None
        if unavailable:
            return self._evaluate_sensor_offline(station, correlation_id=correlation_id)

        self._resolve_sensor_offline(station_id, correlation_id=correlation_id)

        pm25 = float(station["pm25"])
        severity = self._severity(pm25)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT pm25
                    FROM measurements
                    WHERE station_id = %s AND quality_flag = 'valid'
                      AND measured_at >= NOW() - (%s * INTERVAL '1 second')
                    ORDER BY measured_at DESC
                    LIMIT %s
                    """,
                    (station_id, self.stale_after_seconds, self.consecutive_measurements),
                )
                recent_values = [float(row["pm25"]) for row in cur.fetchall()]
                threshold_qualified = self._threshold_is_qualified(recent_values)
                cur.execute(
                    """
                    SELECT * FROM alerts
                    WHERE station_id = %s AND alert_type = 'pm25_threshold'
                      AND rule_version = %s AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (station_id, self.rule_version),
                )
                existing = cur.fetchone()

                if severity is None:
                    if existing:
                        cur.execute(
                            """
                            UPDATE alerts
                            SET status = 'resolved', resolved_at = NOW(), updated_at = NOW(),
                                description = COALESCE(description, '') || ' Auto-resolved after PM2.5 returned below threshold.'
                            WHERE alert_id = %s
                            RETURNING *
                            """,
                            (existing["alert_id"],),
                        )
                        resolved = dict(cur.fetchone())
                        self.audit.record(
                            actor_type="system",
                            actor_role="backend",
                            action="alert.auto_resolve",
                            entity_type="alert",
                            entity_id=str(resolved["alert_id"]),
                            correlation_id=correlation_id,
                            details={"station_id": station_id, "observed_value": pm25},
                            conn=conn,
                        )
                        return resolved
                    return None

                if not threshold_qualified:
                    return dict(existing) if existing else None

                title = f"PM2.5 elevated at {station['station_name']}"
                description = "Valid fresh simulator data exceeded the configured PM2.5 threshold."
                if existing:
                    cur.execute(
                        """
                        UPDATE alerts
                        SET severity = %s, observed_value = %s, threshold_value = %s,
                            title = %s, description = %s, updated_at = NOW()
                        WHERE alert_id = %s
                        RETURNING *
                        """,
                        (severity, pm25, self.warning_threshold, title, description, existing["alert_id"]),
                    )
                    return dict(cur.fetchone())

                alert_id = str(uuid4())
                cur.execute(
                    """
                    INSERT INTO alerts (
                        alert_id, station_id, alert_type, rule_version, severity,
                        observed_value, threshold_value, title, description, status
                    )
                    VALUES (%s, %s, 'pm25_threshold', %s, %s, %s, %s, %s, %s, 'active')
                    RETURNING *
                    """,
                    (alert_id, station_id, self.rule_version, severity, pm25, self.warning_threshold, title, description),
                )
                created = dict(cur.fetchone())
                self.audit.record(
                    actor_type="system",
                    actor_role="backend",
                    action="alert.create",
                    entity_type="alert",
                    entity_id=str(created["alert_id"]),
                    correlation_id=correlation_id,
                    details={"station_id": station_id, "observed_value": pm25, "threshold": self.warning_threshold},
                    conn=conn,
                )
                return created

    def _evaluate_sensor_offline(self, station: dict[str, Any], *, correlation_id: str | None) -> dict[str, Any] | None:
        # Seeded stations have no last_seen value and must not create noisy startup alerts.
        has_seen = station.get("last_seen_at") is not None or station.get("updated_at") is not None
        if not has_seen:
            return None
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT * FROM alerts
                    WHERE station_id = %s AND alert_type = 'sensor_offline'
                      AND rule_version = %s AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (station["station_id"], self.rule_version),
                )
                existing = cur.fetchone()
                if existing:
                    return dict(existing)
                alert_id = str(uuid4())
                cur.execute(
                    """
                    INSERT INTO alerts (
                        alert_id, station_id, alert_type, rule_version, severity,
                        title, description, status
                    )
                    VALUES (%s, %s, 'sensor_offline', %s, 'warning', %s, %s, 'active')
                    RETURNING *
                    """,
                    (
                        alert_id,
                        station["station_id"],
                        self.rule_version,
                        f"Sensor unavailable at {station['station_name']}",
                        "No valid fresh measurement is available for this station.",
                    ),
                )
                created = dict(cur.fetchone())
                self.audit.record(
                    actor_type="system",
                    actor_role="backend",
                    action="alert.sensor_offline",
                    entity_type="alert",
                    entity_id=str(created["alert_id"]),
                    correlation_id=correlation_id,
                    details={"station_id": station["station_id"], "status": station.get("status")},
                    conn=conn,
                )
                return created

    def _resolve_sensor_offline(self, station_id: str, *, correlation_id: str | None) -> None:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE alerts
                    SET status = 'resolved', resolved_at = NOW(), updated_at = NOW()
                    WHERE station_id = %s AND alert_type = 'sensor_offline'
                      AND rule_version = %s AND status = 'active'
                    RETURNING alert_id
                    """,
                    (station_id, self.rule_version),
                )
                row = cur.fetchone()
                if row:
                    self.audit.record(
                        actor_type="system",
                        actor_role="backend",
                        action="alert.sensor_recovered",
                        entity_type="alert",
                        entity_id=str(row["alert_id"]),
                        correlation_id=correlation_id,
                        details={"station_id": station_id},
                        conn=conn,
                    )

    def list_alerts(self, *, status: str | None = None, station_id: str | None = None) -> list[dict[str, Any]]:
        self.evaluate_all_current()
        clauses = []
        params: list[Any] = []
        if status:
            clauses.append("status = %s")
            params.append(status)
        if station_id:
            clauses.append("station_id = %s")
            params.append(station_id)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    f"""
                    SELECT alert_id, station_id, alert_type, rule_version, severity,
                           observed_value, threshold_value, title, description, status,
                           created_at, updated_at, resolved_at
                    FROM alerts
                    {where}
                    ORDER BY created_at DESC
                    """,
                    params,
                )
                return [self._with_source(dict(row)) for row in cur.fetchall()]

    def resolve_alert(self, alert_id: str, *, actor_id: str, actor_role: str, correlation_id: str | None) -> dict[str, Any]:
        if actor_role != "manager":
            raise ServiceError("forbidden", "Only manager role can resolve alerts", 403)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE alerts
                    SET status = 'resolved', resolved_at = COALESCE(resolved_at, NOW()), updated_at = NOW()
                    WHERE alert_id = %s AND status = 'active'
                    RETURNING *
                    """,
                    (alert_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ServiceError("alert_not_found_or_not_active", "Alert was not found or is not active", 404)
                alert = dict(row)
                self.audit.record(
                    actor_type="user",
                    actor_id=actor_id,
                    actor_role=actor_role,
                    action="alert.manual_resolve",
                    entity_type="alert",
                    entity_id=str(alert_id),
                    correlation_id=correlation_id,
                    details={"station_id": alert.get("station_id")},
                    conn=conn,
                )
                return alert

    def _severity(self, pm25: float) -> str | None:
        if pm25 > self.critical_threshold:
            return "critical"
        if pm25 > self.warning_threshold:
            return "warning"
        return None

    def _threshold_is_qualified(self, values: list[float]) -> bool:
        return (
            len(values) >= self.consecutive_measurements
            and all(value > self.warning_threshold for value in values[: self.consecutive_measurements])
        )

    @staticmethod
    def _with_source(alert: dict[str, Any]) -> dict[str, Any]:
        return {**alert, "source": f"backend_alert_rule:{alert['rule_version']}"}
