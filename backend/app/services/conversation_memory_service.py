from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg2.extras import Json

from .database import Database, ServiceError, dict_cursor

_STATION_IDS = frozenset({"S01", "S02", "S03", "S04", "S05"})
_MEMORY_INTENTS = frozenset(
    {
        "current",
        "compare",
        "history",
        "forecast",
        "active_alerts",
        "weather",
        "recommendation",
        "proposal",
        "impact",
        "spatial",
    }
)
_MEMORY_OUTCOMES = frozenset({"answered", "proposal_pending", "created"})


class ConversationMemoryService:
    """Persist bounded semantic conversation state in the backend system of record.

    Raw prompts, generated answers and environmental values are deliberately not
    stored. The Agent receives only validated station identifiers and the last
    canonical intent; every environmental fact still requires a current tool call.
    """

    def __init__(self, db: Database, *, ttl_seconds: int = 86400) -> None:
        if ttl_seconds < 300:
            raise ValueError("Conversation memory TTL must be at least 300 seconds")
        self.db = db
        self.ttl_seconds = ttl_seconds

    def start_or_resume(
        self,
        *,
        conversation_id: str | None,
        owner_id: str,
    ) -> dict[str, Any]:
        normalized_id = self._conversation_id(conversation_id)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT conversation_id, owner_id, semantic_context, turn_count,
                           expires_at
                    FROM agent_conversations
                    WHERE conversation_id = %s
                    FOR UPDATE
                    """,
                    (normalized_id,),
                )
                row = cur.fetchone()
                if row:
                    if str(row["owner_id"]) != owner_id:
                        # Do not disclose whether another user's conversation exists.
                        raise ServiceError(
                            "conversation_not_found",
                            "Conversation was not found",
                            404,
                        )
                    expires_at = row["expires_at"]
                    if expires_at <= datetime.now(UTC):
                        raise ServiceError(
                            "conversation_expired",
                            "Conversation memory has expired; start a new conversation",
                            410,
                        )
                    cur.execute(
                        """
                        UPDATE agent_conversations
                        SET last_seen_at = NOW(),
                            expires_at = NOW() + (%s * INTERVAL '1 second')
                        WHERE conversation_id = %s
                        """,
                        (self.ttl_seconds, normalized_id),
                    )
                    context = self.normalize_context(row.get("semantic_context"))
                    return {
                        "conversation_id": normalized_id,
                        "context": {**context, "turn_count": int(row["turn_count"])},
                    }

                cur.execute(
                    """
                    INSERT INTO agent_conversations (
                        conversation_id, owner_id, semantic_context, turn_count, expires_at
                    ) VALUES (%s, %s, '{}'::JSONB, 0,
                              NOW() + (%s * INTERVAL '1 second'))
                    """,
                    (normalized_id, owner_id, self.ttl_seconds),
                )
        return {
            "conversation_id": normalized_id,
            "context": {"context_version": 1, "station_ids": [], "turn_count": 0},
        }

    def record_agent_result(
        self,
        *,
        conversation_id: str,
        owner_id: str,
        previous_context: dict[str, Any] | None,
        agent_result: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_id = self._conversation_id(conversation_id)
        context = self.derive_semantic_context(previous_context, agent_result)
        with self.db.connection() as conn:
            with dict_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE agent_conversations
                    SET semantic_context = %s,
                        turn_count = turn_count + 1,
                        last_seen_at = NOW(),
                        expires_at = NOW() + (%s * INTERVAL '1 second')
                    WHERE conversation_id = %s
                      AND owner_id = %s
                      AND expires_at > NOW()
                    RETURNING turn_count
                    """,
                    (Json(context), self.ttl_seconds, normalized_id, owner_id),
                )
                row = cur.fetchone()
        if not row:
            raise ServiceError(
                "conversation_write_conflict",
                "Conversation memory could not be updated safely",
                409,
            )
        return {**context, "turn_count": int(row["turn_count"])}

    @staticmethod
    def derive_semantic_context(
        previous_context: dict[str, Any] | None,
        agent_result: dict[str, Any],
    ) -> dict[str, Any]:
        context = ConversationMemoryService.normalize_context(previous_context)
        trace = agent_result.get("trace")
        trace = trace if isinstance(trace, dict) else {}
        outcome = agent_result.get("outcome") or trace.get("final_outcome")
        if outcome not in _MEMORY_OUTCOMES:
            return context

        intent = agent_result.get("intent") or trace.get("intent")
        if intent in _MEMORY_INTENTS:
            context["last_intent"] = intent

        station_ids: list[str] = []
        for arguments in agent_result.get("tool_arguments") or []:
            if not isinstance(arguments, dict):
                continue
            station_id = arguments.get("station_id")
            if isinstance(station_id, str) and station_id.upper() in _STATION_IDS:
                station_ids.append(station_id.upper())
            values = arguments.get("station_ids")
            if isinstance(values, list):
                station_ids.extend(
                    value.upper()
                    for value in values
                    if isinstance(value, str) and value.upper() in _STATION_IDS
                )
        station_ids = list(dict.fromkeys(station_ids))[:5]
        if station_ids:
            context["station_ids"] = station_ids
            context["primary_station_id"] = station_ids[0]
        return context

    @staticmethod
    def normalize_context(value: Any) -> dict[str, Any]:
        raw = value if isinstance(value, dict) else {}
        station_ids = raw.get("station_ids")
        normalized_stations = (
            list(
                dict.fromkeys(
                    station.upper()
                    for station in station_ids
                    if isinstance(station, str) and station.upper() in _STATION_IDS
                )
            )[:5]
            if isinstance(station_ids, list)
            else []
        )
        context: dict[str, Any] = {
            "context_version": 1,
            "station_ids": normalized_stations,
        }
        primary = raw.get("primary_station_id")
        if isinstance(primary, str) and primary.upper() in normalized_stations:
            context["primary_station_id"] = primary.upper()
        elif normalized_stations:
            context["primary_station_id"] = normalized_stations[0]
        intent = raw.get("last_intent")
        if intent in _MEMORY_INTENTS:
            context["last_intent"] = intent
        return context

    @staticmethod
    def _conversation_id(value: str | None) -> str:
        if value is None:
            return str(uuid4())
        try:
            return str(UUID(str(value)))
        except (TypeError, ValueError) as exc:
            raise ServiceError(
                "conversation_id_invalid",
                "conversation_id must be a UUID",
                422,
            ) from exc
