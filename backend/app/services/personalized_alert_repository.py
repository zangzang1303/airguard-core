from __future__ import annotations

from typing import Any
from uuid import uuid4

from psycopg2.extras import Json

from .database import Database, ServiceError, dict_cursor

CHECKLIST_ITEM_KEYS = (
    "close_windows",
    "bring_laundry_inside",
    "reduce_outdoor_activity",
    "check_air_purifier",
)


class PersonalizedAlertRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_preferences(self, user_id: str) -> dict[str, bool]:
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        SELECT environmental_email_enabled, predictive_email_enabled
                        FROM resident_notification_preferences
                        WHERE user_id = %s
                        """,
                        (user_id,),
                    )
                    row = cur.fetchone()
            return {
                "environmental_email_enabled": bool(row and row["environmental_email_enabled"]),
                "predictive_email_enabled": bool(row and row["predictive_email_enabled"]),
            }
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError("notification_preferences_unavailable", "Notification preferences are unavailable", 503) from exc

    def update_preferences(self, user_id: str, values: dict[str, bool]) -> dict[str, bool]:
        current = self.get_preferences(user_id)
        merged = {**current, **values}
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        """
                        INSERT INTO resident_notification_preferences (
                            user_id, environmental_email_enabled, predictive_email_enabled
                        ) VALUES (%s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            environmental_email_enabled = EXCLUDED.environmental_email_enabled,
                            predictive_email_enabled = EXCLUDED.predictive_email_enabled,
                            updated_at = NOW()
                        RETURNING environmental_email_enabled, predictive_email_enabled
                        """,
                        (
                            user_id,
                            merged["environmental_email_enabled"],
                            merged["predictive_email_enabled"],
                        ),
                    )
                    row = cur.fetchone()
            return {
                "environmental_email_enabled": bool(row["environmental_email_enabled"]),
                "predictive_email_enabled": bool(row["predictive_email_enabled"]),
            }
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError("notification_preferences_unavailable", "Notification preferences could not be updated", 503) from exc

    def list_predictive_recipients(self) -> list[dict[str, str]]:
        return self._list_recipients("predictive_email_enabled")

    def list_environmental_recipients(self) -> list[dict[str, str]]:
        return self._list_recipients("environmental_email_enabled")

    def _list_recipients(self, preference_column: str) -> list[dict[str, str]]:
        if preference_column not in {"predictive_email_enabled", "environmental_email_enabled"}:
            raise ValueError("unsupported preference column")
        try:
            with self.db.connection() as conn:
                with dict_cursor(conn) as cur:
                    cur.execute(
                        f"""
                        SELECT u.user_id, u.email, u.sensitivity_group
                        FROM users u
                        JOIN resident_notification_preferences p ON p.user_id = u.user_id
                        WHERE u.role = 'resident'
                          AND u.is_active = TRUE
                          AND u.email_verified_at IS NOT NULL
                          AND u.email IS NOT NULL
                          AND BTRIM(u.email) <> ''
                          AND p.{preference_column} = TRUE
                        ORDER BY u.user_id
                        """
                    )
                    rows = cur.fetchall()
            return [
                {
                    "user_id": str(row["user_id"]),
                    "email": str(row["email"]),
                    "sensitivity_group": str(row.get("sensitivity_group") or "normal"),
                }
                for row in rows
            ]
        except Exception as exc:
            raise ServiceError("notification_recipient_unavailable", "Notification recipients are unavailable", 503) from exc

    def get_predictive_recipient(self, user_id: str) -> dict[str, str] | None:
        return next((row for row in self.list_predictive_recipients() if row["user_id"] == user_id), None)

    def has_active_pm25_alert(self, station_id: str) -> bool:
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM alerts
                    WHERE station_id = %s AND alert_type = 'pm25_threshold' AND status = 'active'
                    LIMIT 1
                    """,
                    (station_id,),
                )
                return cur.fetchone() is not None

    def get_active_episode(self, station_id: str, threshold_rule_version: str) -> dict[str, Any] | None:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT * FROM predictive_warning_episodes
                    WHERE station_id = %s AND metric = 'pm25'
                      AND threshold_rule_version = %s AND status = 'active'
                    """,
                    (station_id, threshold_rule_version),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def upsert_active_episode(self, candidate: dict[str, Any]) -> dict[str, Any]:
        episode_id = str(candidate.get("episode_id") or uuid4())
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO predictive_warning_episodes (
                        episode_id, station_id, metric, status, severity,
                        threshold_value, threshold_rule_version, policy_version,
                        forecast_generated_at, forecast_target_at, predicted_value,
                        predicted_min, predicted_max, confidence, model_version,
                        source, evidence, clear_evaluation_count
                    ) VALUES (
                        %s, %s, 'pm25', 'active', %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0
                    )
                    ON CONFLICT (station_id, metric, threshold_rule_version)
                    WHERE status = 'active'
                    DO UPDATE SET
                        severity = EXCLUDED.severity,
                        threshold_value = EXCLUDED.threshold_value,
                        policy_version = EXCLUDED.policy_version,
                        forecast_generated_at = EXCLUDED.forecast_generated_at,
                        forecast_target_at = EXCLUDED.forecast_target_at,
                        predicted_value = EXCLUDED.predicted_value,
                        predicted_min = EXCLUDED.predicted_min,
                        predicted_max = EXCLUDED.predicted_max,
                        confidence = EXCLUDED.confidence,
                        model_version = EXCLUDED.model_version,
                        source = EXCLUDED.source,
                        evidence = EXCLUDED.evidence,
                        clear_evaluation_count = 0,
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (
                        episode_id,
                        candidate["station_id"],
                        candidate["severity"],
                        candidate["threshold_value"],
                        candidate["threshold_rule_version"],
                        candidate["policy_version"],
                        candidate["forecast_generated_at"],
                        candidate["forecast_target_at"],
                        candidate["predicted_value"],
                        candidate["predicted_min"],
                        candidate["predicted_max"],
                        candidate["confidence"],
                        candidate["model_version"],
                        candidate["source"],
                        Json(candidate["evidence"]),
                    ),
                )
                row = cur.fetchone()
        return dict(row)

    def increment_clear(self, episode_id: str) -> dict[str, Any]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE predictive_warning_episodes
                    SET clear_evaluation_count = clear_evaluation_count + 1, updated_at = NOW()
                    WHERE episode_id = %s AND status = 'active'
                    RETURNING *
                    """,
                    (episode_id,),
                )
                row = cur.fetchone()
        if not row:
            raise ServiceError("predictive_warning_not_found", "Active predictive warning was not found", 404)
        return dict(row)

    def transition_episode(self, episode_id: str, status: str) -> dict[str, Any]:
        if status not in {"observed", "resolved", "expired"}:
            raise ValueError("invalid terminal status")
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE predictive_warning_episodes
                    SET status = %s, resolved_at = NOW(), updated_at = NOW()
                    WHERE episode_id = %s AND status = 'active'
                    RETURNING *
                    """,
                    (status, episode_id),
                )
                row = cur.fetchone()
        if not row:
            raise ServiceError("predictive_warning_not_found", "Active predictive warning was not found", 404)
        return dict(row)

    def mark_notified(self, episode_id: str) -> None:
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE predictive_warning_episodes SET notified_at = NOW() WHERE episode_id = %s",
                    (episode_id,),
                )

    def get_episode(self, episode_id: str) -> dict[str, Any]:
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute("SELECT * FROM predictive_warning_episodes WHERE episode_id = %s", (episode_id,))
                row = cur.fetchone()
        if not row:
            raise ServiceError("predictive_warning_not_found", "Predictive warning was not found", 404)
        return dict(row)

    def list_episodes(self, *, status: str | None = None, station_id: str | None = None) -> list[dict[str, Any]]:
        if status is not None and status not in {"active", "observed", "resolved", "expired"}:
            raise ServiceError("invalid_predictive_warning_status", "Unsupported predictive warning status", 422)
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = %s")
            params.append(status)
        if station_id:
            clauses.append("station_id = %s")
            params.append(station_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    f"SELECT * FROM predictive_warning_episodes {where} ORDER BY created_at DESC",
                    tuple(params),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def get_checklist(self, episode_id: str, user_id: str) -> list[dict[str, Any]]:
        self.get_episode(episode_id)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT item_key, completed, updated_at
                    FROM warning_checklist_responses
                    WHERE episode_id = %s AND user_id = %s
                    """,
                    (episode_id, user_id),
                )
                persisted = {row["item_key"]: dict(row) for row in cur.fetchall()}
        return [
            persisted.get(key, {"item_key": key, "completed": False, "updated_at": None})
            for key in CHECKLIST_ITEM_KEYS
        ]

    def put_checklist(self, episode_id: str, user_id: str, item_key: str, completed: bool) -> dict[str, Any]:
        if item_key not in CHECKLIST_ITEM_KEYS:
            raise ServiceError("invalid_checklist_item", "Checklist item is unsupported", 422)
        self.get_episode(episode_id)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO warning_checklist_responses (episode_id, user_id, item_key, completed)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (episode_id, user_id, item_key) DO UPDATE SET
                        completed = EXCLUDED.completed,
                        updated_at = NOW()
                    RETURNING item_key, completed, updated_at
                    """,
                    (episode_id, user_id, item_key, completed),
                )
                row = cur.fetchone()
        return dict(row)
