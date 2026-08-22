from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import psycopg2
import psycopg2.extras


@dataclass
class ServiceError(Exception):
    code: str
    message: str
    status_code: int = 500
    details: dict[str, Any] | None = None


class Database:
    def __init__(self, database_url: str | None) -> None:
        self.database_url = database_url

    @contextmanager
    def connection(self) -> Iterator[Any]:
        if not self.database_url:
            raise ServiceError("database_not_configured", "DATABASE_URL is not configured", 503)
        try:
            conn = psycopg2.connect(self.database_url)
        except psycopg2.Error as exc:
            raise ServiceError("database_unavailable", "PostgreSQL is unavailable", 503) from exc
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def ping(self) -> None:
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")


def dict_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
