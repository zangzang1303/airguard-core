from __future__ import annotations

import os
from datetime import UTC, datetime
from threading import RLock
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://airguard:airguard@localhost:5432/airguard")
PERSIST_JOBS = os.getenv("JOB_PERSISTENCE_ENABLED", "false").lower() in {"1", "true", "yes", "on"}

_jobs: dict[str, dict[str, Any]] = {}
_idempotency_index: dict[str, str] = {}
_lock = RLock()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _connect():
    return psycopg2.connect(DATABASE_URL, connect_timeout=2)


def _normalize(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    normalized = dict(record)
    for key in ("created_at", "started_at", "finished_at", "updated_at"):
        value = normalized.get(key)
        if isinstance(value, datetime):
            normalized[key] = value.isoformat()
    if "result_payload" in normalized:
        normalized["result"] = normalized.pop("result_payload")
    if "request_payload" in normalized:
        normalized["request"] = normalized.pop("request_payload")
    return normalized


def reserve_job(
    task_id: str,
    job_type: str,
    idempotency_key: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    index_key = f"{job_type}:{idempotency_key}"
    with _lock:
        existing_id = _idempotency_index.get(index_key)
        if existing_id:
            return get_job(existing_id) or dict(_jobs[existing_id]), False
        record = {
            "task_id": task_id,
            "job_type": job_type,
            "idempotency_key": idempotency_key,
            "status": "PENDING",
            "request": payload,
            "result": None,
            "error_message": None,
            "attempt_count": 0,
            "created_at": _now(),
            "started_at": None,
            "finished_at": None,
            "updated_at": _now(),
        }
        _jobs[task_id] = record
        _idempotency_index[index_key] = task_id

    if PERSIST_JOBS:
        try:
            with _connect() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO job_runs (
                        task_id, job_type, idempotency_key, status, request_payload
                    ) VALUES (%s, %s, %s, 'PENDING', %s)
                    ON CONFLICT (job_type, idempotency_key) DO NOTHING
                    """,
                    (task_id, job_type, idempotency_key, Json(payload)),
                )
                inserted = cursor.rowcount == 1
                cursor.execute(
                    "SELECT * FROM job_runs WHERE job_type = %s AND idempotency_key = %s",
                    (job_type, idempotency_key),
                )
                persisted = _normalize(cursor.fetchone())
            if persisted:
                with _lock:
                    _jobs.pop(task_id, None)
                    _jobs[persisted["task_id"]] = persisted
                    _idempotency_index[index_key] = persisted["task_id"]
                if not inserted:
                    return persisted, False
        except psycopg2.Error:
            pass

    return dict(record), True


def get_job(task_id: str) -> dict[str, Any] | None:
    if PERSIST_JOBS:
        try:
            with _connect() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM job_runs WHERE task_id = %s", (task_id,))
                persisted = _normalize(cursor.fetchone())
            if persisted:
                with _lock:
                    _jobs[task_id] = persisted
                return persisted
        except psycopg2.Error:
            pass

    with _lock:
        record = _jobs.get(task_id)
        return dict(record) if record else None


def _update_local(task_id: str, **changes: Any) -> None:
    with _lock:
        if task_id in _jobs:
            _jobs[task_id].update(changes)
            _jobs[task_id]["updated_at"] = _now()


def mark_job_running(task_id: str) -> None:
    existing = get_job(task_id) or {}
    _update_local(
        task_id,
        status="STARTED",
        started_at=existing.get("started_at") or _now(),
        attempt_count=int(existing.get("attempt_count", 0)) + 1,
    )
    _update_database(
        """
        UPDATE job_runs
        SET status = 'STARTED', started_at = COALESCE(started_at, NOW()),
            attempt_count = attempt_count + 1, updated_at = NOW()
        WHERE task_id = %s
        """,
        (task_id,),
    )


def mark_job_succeeded(task_id: str, result: dict[str, Any]) -> None:
    _update_local(task_id, status="SUCCESS", result=result, error_message=None, finished_at=_now())
    _update_database(
        """
        UPDATE job_runs
        SET status = 'SUCCESS', result_payload = %s, error_message = NULL,
            finished_at = NOW(), updated_at = NOW()
        WHERE task_id = %s
        """,
        (Json(result), task_id),
    )


def mark_job_failed(task_id: str, error: str, *, retrying: bool) -> None:
    status = "RETRY" if retrying else "FAILURE"
    changes: dict[str, Any] = {"status": status, "error_message": error}
    if not retrying:
        changes["finished_at"] = _now()
    _update_local(task_id, **changes)
    _update_database(
        """
        UPDATE job_runs
        SET status = %s, error_message = %s,
            finished_at = CASE WHEN %s = 'FAILURE' THEN NOW() ELSE finished_at END,
            updated_at = NOW()
        WHERE task_id = %s
        """,
        (status, error, status, task_id),
    )


def _update_database(query: str, params: tuple[Any, ...]) -> None:
    if not PERSIST_JOBS:
        return
    try:
        with _connect() as connection, connection.cursor() as cursor:
            cursor.execute(query, params)
    except psycopg2.Error:
        pass
