from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from backend.app.services.conversation_memory_service import ConversationMemoryService
from backend.app.services.database import ServiceError


class FakeCursor:
    def __init__(self, select_row: dict[str, Any] | None = None, update_turn: int = 1) -> None:
        self.select_row = select_row
        self.update_turn = update_turn
        self.current: dict[str, Any] | None = None
        self.calls: list[tuple[str, tuple[Any, ...] | None]] = []

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        compact = " ".join(query.split())
        self.calls.append((compact, params))
        if compact.startswith("SELECT conversation_id"):
            self.current = self.select_row
        elif "RETURNING turn_count" in compact:
            self.current = {"turn_count": self.update_turn}
        else:
            self.current = None

    def fetchone(self) -> dict[str, Any] | None:
        return self.current


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.fake_cursor = cursor

    def cursor(self, **_kwargs: Any) -> FakeCursor:
        return self.fake_cursor


class FakeDatabase:
    def __init__(self, cursor: FakeCursor) -> None:
        self.cursor = cursor

    @contextmanager
    def connection(self):
        yield FakeConnection(self.cursor)


def test_new_conversation_stores_no_raw_prompt_or_environmental_fact() -> None:
    cursor = FakeCursor(select_row=None)
    service = ConversationMemoryService(FakeDatabase(cursor), ttl_seconds=3600)  # type: ignore[arg-type]

    record = service.start_or_resume(
        conversation_id="11111111-1111-4111-8111-111111111111",
        owner_id="demo-user",
    )

    assert record["context"] == {"context_version": 1, "station_ids": [], "turn_count": 0}
    insert = next(call for call in cursor.calls if call[0].startswith("INSERT INTO agent_conversations"))
    assert insert[1] is not None
    assert (str(insert[1][0]), *insert[1][1:]) == (
        "11111111-1111-4111-8111-111111111111",
        "demo-user",
        3600,
    )


def test_conversation_owner_isolation_does_not_disclose_foreign_record() -> None:
    cursor = FakeCursor(
        select_row={
            "conversation_id": "11111111-1111-4111-8111-111111111111",
            "owner_id": "user-a",
            "semantic_context": {"station_ids": ["S03"]},
            "turn_count": 2,
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
        }
    )
    service = ConversationMemoryService(FakeDatabase(cursor), ttl_seconds=3600)  # type: ignore[arg-type]

    with pytest.raises(ServiceError) as exc_info:
        service.start_or_resume(
            conversation_id="11111111-1111-4111-8111-111111111111",
            owner_id="user-b",
        )

    assert exc_info.value.code == "conversation_not_found"
    assert exc_info.value.status_code == 404


def test_expired_conversation_requires_a_new_thread() -> None:
    cursor = FakeCursor(
        select_row={
            "conversation_id": "11111111-1111-4111-8111-111111111111",
            "owner_id": "demo-user",
            "semantic_context": {"station_ids": ["S03"]},
            "turn_count": 2,
            "expires_at": datetime.now(UTC) - timedelta(seconds=1),
        }
    )
    service = ConversationMemoryService(FakeDatabase(cursor), ttl_seconds=3600)  # type: ignore[arg-type]

    with pytest.raises(ServiceError) as exc_info:
        service.start_or_resume(
            conversation_id="11111111-1111-4111-8111-111111111111",
            owner_id="demo-user",
        )

    assert exc_info.value.code == "conversation_expired"
    assert exc_info.value.status_code == 410


def test_only_successful_canonical_route_updates_semantic_memory() -> None:
    previous = {
        "context_version": 1,
        "station_ids": ["S03"],
        "primary_station_id": "S03",
        "last_intent": "current",
        "raw_prompt": "must be removed",
        "aqi": 999,
    }

    failed = ConversationMemoryService.derive_semantic_context(
        previous,
        {
            "intent": "forecast",
            "outcome": "insufficient_data",
            "tool_arguments": [{"station_id": "S05", "hours": 3}],
        },
    )
    assert failed == {
        "context_version": 1,
        "station_ids": ["S03"],
        "primary_station_id": "S03",
        "last_intent": "current",
    }

    answered = ConversationMemoryService.derive_semantic_context(
        failed,
        {
            "intent": "compare",
            "outcome": "answered",
            "tool_arguments": [{"station_ids": ["S03", "S04"]}],
            "answer": "AQI values must not be persisted",
            "sources": [{"aqi": 123}],
        },
    )
    assert answered == {
        "context_version": 1,
        "station_ids": ["S03", "S04"],
        "primary_station_id": "S03",
        "last_intent": "compare",
    }


def test_record_result_advances_turn_count() -> None:
    cursor = FakeCursor(update_turn=4)
    service = ConversationMemoryService(FakeDatabase(cursor), ttl_seconds=3600)  # type: ignore[arg-type]

    context = service.record_agent_result(
        conversation_id="11111111-1111-4111-8111-111111111111",
        owner_id="demo-user",
        previous_context={"station_ids": ["S03"], "last_intent": "current"},
        agent_result={
            "intent": "forecast",
            "outcome": "answered",
            "tool_arguments": [{"station_id": "S03", "hours": 3}],
        },
    )

    assert context["turn_count"] == 4
    assert context["last_intent"] == "forecast"
    assert context["station_ids"] == ["S03"]
