from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal
from urllib.parse import quote

import httpx
from langchain_openai import ChatOpenAI

from src.config import Settings, get_settings

LlmProvider = Literal["openai", "agentrouter", "gemini"]


class LlmProviderError(RuntimeError):
    """A sanitized provider-boundary failure safe to expose by exception type."""


def normalize_llm_exception(exc: Exception) -> LlmProviderError:
    """Map provider-client failures to stable, non-sensitive failure codes."""
    if isinstance(exc, LlmProviderError):
        return exc
    if isinstance(exc, (TimeoutError, httpx.TimeoutException)):
        return LlmProviderError("provider_timeout")
    if isinstance(exc, httpx.HTTPError):
        return LlmProviderError("provider_network_error")
    return LlmProviderError("provider_unexpected_error")


@dataclass(frozen=True)
class LlmReply:
    content: str
    usage_metadata: dict[str, int]


class AgentRouterClaudeClient:
    """Anthropic-Messages client for Claude models served by AgentRouter."""

    provider = "agentrouter"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float,
        timeout_seconds: float,
        max_tokens: int,
        max_retries: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key or not model:
            raise LlmProviderError("agentrouter configuration is incomplete")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self._client = client

    async def ainvoke(self, prompt: str) -> LlmReply:
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key,
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json",
        }
        endpoint = "/messages" if self.base_url.endswith("/v1") else "/v1/messages"
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds)
        try:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(endpoint, headers=headers, json=payload)
                except httpx.TimeoutException as exc:
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.1 * (attempt + 1))
                        continue
                    raise LlmProviderError("provider_timeout") from exc
                except httpx.HTTPError as exc:
                    raise LlmProviderError("provider_network_error") from exc

                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                if response.status_code in {401, 403}:
                    raise LlmProviderError("provider_authentication_failed")
                if response.status_code >= 400:
                    raise LlmProviderError(f"provider_http_{response.status_code}")
                return _parse_agentrouter_reply(response)
            raise LlmProviderError("provider_retry_exhausted")
        finally:
            if owns_client:
                await client.aclose()


class GeminiGenerateContentClient:
    """Google Gemini Generate Content client with a bounded failure policy."""

    provider = "gemini"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float,
        timeout_seconds: float,
        max_tokens: int,
        max_retries: int,
        thinking_level: str,
        retry_base_seconds: float = 1.0,
        retry_max_seconds: float = 60.0,
        client: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if not api_key or not model:
            raise LlmProviderError("gemini configuration is incomplete")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.thinking_level = thinking_level
        self.retry_base_seconds = retry_base_seconds
        self.retry_max_seconds = retry_max_seconds
        self._client = client
        self._sleep = sleep

    async def ainvoke(self, prompt: str) -> LlmReply:
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "thinkingConfig": {"thinkingLevel": self.thinking_level.upper()},
            },
        }
        endpoint = f"{self.base_url}/models/{quote(self.model, safe='-_.')}:generateContent"
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self.timeout_seconds)
        try:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(
                        endpoint,
                        headers={"x-goog-api-key": self.api_key, "content-type": "application/json"},
                        json=payload,
                    )
                except httpx.TimeoutException as exc:
                    if attempt < self.max_retries:
                        await self._sleep(self._retry_delay(attempt))
                        continue
                    raise LlmProviderError("provider_timeout") from exc
                except httpx.HTTPError as exc:
                    raise LlmProviderError("provider_network_error") from exc

                if response.status_code == 429:
                    failure_code, retryable, retry_after = _gemini_quota_policy(response)
                    if retryable and attempt < self.max_retries:
                        await self._sleep(self._retry_delay(attempt, retry_after))
                        continue
                    raise LlmProviderError(failure_code)
                if response.status_code in {500, 502, 503, 504} and attempt < self.max_retries:
                    await self._sleep(self._retry_delay(attempt))
                    continue
                if response.status_code in {401, 403}:
                    raise LlmProviderError("provider_authentication_failed")
                if response.status_code >= 400:
                    raise LlmProviderError(f"provider_http_{response.status_code}")
                return _parse_gemini_reply(response)
            raise LlmProviderError("provider_retry_exhausted")
        finally:
            if owns_client:
                await client.aclose()

    def _retry_delay(self, attempt: int, server_delay: float | None = None) -> float:
        delay = server_delay
        if delay is None:
            delay = self.retry_base_seconds * (2**attempt)
        return min(delay, self.retry_max_seconds)


def resolve_llm_provider(settings: Any) -> LlmProvider | None:
    configured = getattr(settings, "llm_provider", "auto")
    gemini_ready = bool(getattr(settings, "gemini_api_key", "") and getattr(settings, "gemini_model", ""))
    agentrouter_ready = bool(
        getattr(settings, "agentrouter_api_key", "") and getattr(settings, "agentrouter_model", "")
    )
    openai_ready = bool(getattr(settings, "openai_api_key", ""))
    if configured == "gemini":
        return "gemini" if gemini_ready else None
    if configured == "agentrouter":
        return "agentrouter" if agentrouter_ready else None
    if configured == "openai":
        return "openai" if openai_ready else None
    if gemini_ready:
        return "gemini"
    if agentrouter_ready:
        return "agentrouter"
    if openai_ready:
        return "openai"
    return None


def resolved_model_name(settings: Any, provider: LlmProvider) -> str:
    if provider == "gemini":
        return str(getattr(settings, "gemini_model", "gemini-3.6-flash"))
    if provider == "agentrouter":
        return str(getattr(settings, "agentrouter_model", ""))
    return str(getattr(settings, "model_name", "gpt-4o-mini"))


def get_llm(*, settings: Settings | None = None) -> Any:
    settings = settings or get_settings()
    provider = resolve_llm_provider(settings)
    if provider == "gemini":
        return _cached_gemini_client(
            settings.gemini_api_key,
            settings.gemini_base_url,
            settings.gemini_model,
            settings.llm_timeout_seconds,
            settings.gemini_max_tokens,
            settings.llm_max_retries,
            settings.gemini_thinking_level,
            settings.gemini_retry_base_seconds,
            settings.gemini_retry_max_seconds,
        )
    if provider == "agentrouter":
        return AgentRouterClaudeClient(
            api_key=settings.agentrouter_api_key,
            base_url=settings.agentrouter_base_url,
            model=settings.agentrouter_model,
            temperature=settings.llm_temperature,
            timeout_seconds=settings.llm_timeout_seconds,
            max_tokens=settings.llm_max_tokens,
            max_retries=settings.llm_max_retries,
        )
    if provider == "openai":
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
            max_tokens=settings.llm_max_tokens,
            max_retries=settings.llm_max_retries,
        )
    raise LlmProviderError("no live LLM provider is configured")


@lru_cache(maxsize=4)
def _cached_gemini_client(
    api_key: str,
    base_url: str,
    model: str,
    timeout_seconds: float,
    max_tokens: int,
    max_retries: int,
    thinking_level: str,
    retry_base_seconds: float,
    retry_max_seconds: float,
) -> GeminiGenerateContentClient:
    return GeminiGenerateContentClient(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
        timeout_seconds=timeout_seconds,
        max_tokens=max_tokens,
        max_retries=max_retries,
        thinking_level=thinking_level,
        retry_base_seconds=retry_base_seconds,
        retry_max_seconds=retry_max_seconds,
        client=httpx.AsyncClient(timeout=timeout_seconds),
    )


def _gemini_quota_policy(response: httpx.Response) -> tuple[str, bool, float | None]:
    """Return a sanitized failure code, retryability, and provider retry delay."""
    retry_after: float | None = None
    quota_ids: list[str] = []
    try:
        details = response.json().get("error", {}).get("details", [])
        for detail in details:
            if not isinstance(detail, dict):
                continue
            detail_type = str(detail.get("@type", ""))
            if detail_type.endswith("RetryInfo"):
                retry_after = _parse_google_duration(detail.get("retryDelay"))
            elif detail_type.endswith("QuotaFailure"):
                for violation in detail.get("violations", []):
                    if isinstance(violation, dict):
                        quota_ids.append(str(violation.get("quotaId", "")))
    except (TypeError, ValueError):
        pass

    if any("PerDay" in quota_id for quota_id in quota_ids):
        return "provider_daily_quota_exhausted", False, retry_after
    return "provider_rate_limited", True, retry_after


def _parse_google_duration(value: Any) -> float | None:
    match = re.fullmatch(r"(\d+(?:\.\d+)?)s", str(value or ""))
    if not match:
        return None
    return float(match.group(1))


def _parse_agentrouter_reply(response: httpx.Response) -> LlmReply:
    try:
        payload = response.json()
        content = payload["content"]
        text = "".join(
            str(block.get("text", ""))
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
        if not text:
            raise ValueError("missing text content")
        usage = payload.get("usage") or {}
        return LlmReply(
            content=text,
            usage_metadata={
                "input_tokens": int(usage.get("input_tokens", 0)),
                "output_tokens": int(usage.get("output_tokens", 0)),
            },
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise LlmProviderError("provider_malformed_response") from exc


def _parse_gemini_reply(response: httpx.Response) -> LlmReply:
    try:
        payload = response.json()
        parts = payload["candidates"][0]["content"]["parts"]
        text = "".join(
            str(part.get("text", "")) for part in parts if isinstance(part, dict) and part.get("text")
        ).strip()
        if not text:
            raise ValueError("missing text content")
        usage = payload.get("usageMetadata") or {}
        return LlmReply(
            content=text,
            usage_metadata={
                "input_tokens": int(usage.get("promptTokenCount", 0)),
                "output_tokens": int(usage.get("candidatesTokenCount", 0)),
                "total_tokens": int(usage.get("totalTokenCount", 0)),
            },
        )
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise LlmProviderError("provider_malformed_response") from exc
