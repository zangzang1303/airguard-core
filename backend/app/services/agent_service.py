from __future__ import annotations

from typing import Any

import httpx


class AgentServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class AgentService:
    """HTTP boundary from the system-of-record backend to the isolated Agent service."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 8.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def chat(
        self,
        *,
        message: str,
        user_id: str,
        station_id: str | None,
        request_id: str,
        conversation: list[dict[str, str]] | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self._payload(
            message=message,
            user_id=user_id,
            station_id=station_id,
            conversation=conversation,
            conversation_context=conversation_context,
        )
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    "/api/v1/agent/chat",
                    json=payload,
                    headers={"X-Request-ID": request_id},
                )
        except httpx.TimeoutException as exc:
            raise AgentServiceError("agent_timeout", "Agent service timed out", 503) from exc
        except httpx.HTTPError as exc:
            raise AgentServiceError("agent_unavailable", "Agent service is unavailable", 503) from exc
        return self._validated_response(response, request_id=request_id)

    def chat_sync(
        self,
        *,
        message: str,
        user_id: str,
        station_id: str | None,
        request_id: str,
        conversation: list[dict[str, str]] | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self._payload(
            message=message,
            user_id=user_id,
            station_id=station_id,
            conversation=conversation,
            conversation_context=conversation_context,
        )
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds) as client:
                response = client.post(
                    "/api/v1/agent/chat",
                    json=payload,
                    headers={"X-Request-ID": request_id},
                )
        except httpx.TimeoutException as exc:
            raise AgentServiceError("agent_timeout", "Agent service timed out", 503) from exc
        except httpx.HTTPError as exc:
            raise AgentServiceError("agent_unavailable", "Agent service is unavailable", 503) from exc
        return self._validated_response(response, request_id=request_id)

    @staticmethod
    def _payload(
        *,
        message: str,
        user_id: str,
        station_id: str | None,
        conversation: list[dict[str, str]] | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": message, "user_id": user_id}
        if station_id:
            payload["station_id"] = station_id
        if conversation:
            payload["conversation"] = conversation
        if conversation_context:
            payload["conversation_context"] = conversation_context
        return payload

    @staticmethod
    def _validated_response(response: httpx.Response, *, request_id: str) -> dict[str, Any]:
        if response.status_code >= 400:
            status_code = 422 if response.status_code == 422 else 503
            raise AgentServiceError(
                "agent_request_rejected" if status_code == 422 else "agent_unavailable",
                "Agent service could not process the request",
                status_code,
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise AgentServiceError("agent_schema_drift", "Agent service returned invalid JSON", 503) from exc
        required = {"answer", "used_tools", "sources", "request_id", "trace"}
        if not isinstance(data, dict) or not required.issubset(data):
            raise AgentServiceError("agent_schema_drift", "Agent service response is missing required fields", 503)
        if data["request_id"] != request_id:
            raise AgentServiceError("agent_correlation_mismatch", "Agent response correlation id did not match", 503)
        return data
