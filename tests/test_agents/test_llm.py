from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from src.services.llm import (
    AgentRouterClaudeClient,
    GeminiGenerateContentClient,
    LlmProviderError,
    get_llm,
    resolve_llm_provider,
)


def _client(http_client: httpx.AsyncClient) -> AgentRouterClaudeClient:
    return AgentRouterClaudeClient(
        api_key="local-test-key",
        base_url="https://agentrouter.test",
        model="claude-test",
        temperature=0.2,
        timeout_seconds=1,
        max_tokens=80,
        max_retries=1,
        client=http_client,
    )


def _gemini_client(
    http_client: httpx.AsyncClient,
    *,
    sleep: AsyncMock | None = None,
) -> GeminiGenerateContentClient:
    return GeminiGenerateContentClient(
        api_key="local-gemini-key",
        base_url="https://gemini.test/v1beta",
        model="gemini-3.6-flash",
        temperature=0.2,
        timeout_seconds=1,
        max_tokens=80,
        max_retries=1,
        thinking_level="minimal",
        client=http_client,
        sleep=sleep or AsyncMock(),
    )


@pytest.mark.asyncio
async def test_agentrouter_uses_anthropic_messages_contract_and_maps_usage():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/messages"
        assert request.headers["anthropic-version"] == "2023-06-01"
        payload = __import__("json").loads(request.content)
        assert payload["model"] == "claude-test"
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "Giới hạn đã được nêu rõ."}],
                "usage": {"input_tokens": 7, "output_tokens": 5},
            },
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://agentrouter.test"
    ) as http_client:
        reply = await _client(http_client).ainvoke("Explain safely")

    assert reply.content == "Giới hạn đã được nêu rõ."
    assert reply.usage_metadata == {"input_tokens": 7, "output_tokens": 5}


@pytest.mark.asyncio
async def test_agentrouter_retries_transient_http_failure_once():
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"error": "temporary"})
        return httpx.Response(200, json={"content": [{"type": "text", "text": "An toàn."}]})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://agentrouter.test"
    ) as http_client:
        reply = await _client(http_client).ainvoke("Explain safely")

    assert reply.content == "An toàn."
    assert calls == 2


@pytest.mark.asyncio
async def test_agentrouter_malformed_output_fails_closed():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={"content": []})),
        base_url="https://agentrouter.test",
    ) as http_client:
        with pytest.raises(LlmProviderError, match="malformed"):
            await _client(http_client).ainvoke("Explain safely")


def test_auto_provider_prefers_configured_agentrouter_claude():
    settings = SimpleNamespace(
        llm_provider="auto",
        agentrouter_api_key="router-key",
        agentrouter_model="claude-test",
        openai_api_key="openai-key",
    )

    assert resolve_llm_provider(settings) == "agentrouter"


def test_openai_client_receives_configured_base_url(monkeypatch):
    captured: dict[str, object] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    import src.services.llm as llm_module

    monkeypatch.setattr(llm_module, "ChatOpenAI", FakeChatOpenAI)
    settings = SimpleNamespace(
        llm_provider="openai",
        openai_api_key="openai-key",
        openai_base_url="https://openai-compatible.test/v1",
        model_name="gpt-4o",
        llm_temperature=0.2,
        llm_timeout_seconds=6.0,
        llm_max_tokens=280,
        llm_max_retries=1,
    )

    get_llm(settings=settings)

    assert captured["model"] == "gpt-4o"
    assert captured["base_url"] == "https://openai-compatible.test/v1"


@pytest.mark.asyncio
async def test_gemini_uses_generate_content_contract_and_maps_usage():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1beta/models/gemini-3.6-flash:generateContent"
        assert request.headers["x-goog-api-key"] == "local-gemini-key"
        payload = __import__("json").loads(request.content)
        assert payload["contents"][0]["parts"][0]["text"] == "Explain safely"
        assert payload["generationConfig"]["maxOutputTokens"] == 80
        assert payload["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "MINIMAL"
        assert "temperature" not in payload["generationConfig"]
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "Giới hạn đã được nêu rõ."}]}}],
                "usageMetadata": {
                    "promptTokenCount": 8,
                    "candidatesTokenCount": 6,
                    "totalTokenCount": 14,
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        reply = await _gemini_client(http_client).ainvoke("Explain safely")

    assert reply.content == "Giới hạn đã được nêu rõ."
    assert reply.usage_metadata == {"input_tokens": 8, "output_tokens": 6, "total_tokens": 14}


@pytest.mark.asyncio
async def test_gemini_malformed_output_fails_closed():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={"candidates": []}))
    ) as http_client:
        with pytest.raises(LlmProviderError, match="malformed"):
            await _gemini_client(http_client).ainvoke("Explain safely")


@pytest.mark.asyncio
async def test_gemini_honors_retry_info_for_short_term_rate_limit():
    calls = 0
    sleep = AsyncMock()

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                429,
                json={
                    "error": {
                        "details": [
                            {
                                "@type": "type.googleapis.com/google.rpc.RetryInfo",
                                "retryDelay": "9s",
                            },
                            {
                                "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                                "violations": [{"quotaId": "GenerateRequestsPerMinute"}],
                            },
                        ]
                    }
                },
            )
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "An toàn."}]}}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        reply = await _gemini_client(http_client, sleep=sleep).ainvoke("Explain safely")

    assert reply.content == "An toàn."
    assert calls == 2
    sleep.assert_awaited_once_with(9.0)


@pytest.mark.asyncio
async def test_gemini_does_not_retry_exhausted_daily_quota():
    calls = 0
    sleep = AsyncMock()

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            429,
            json={
                "error": {
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.RetryInfo",
                            "retryDelay": "33s",
                        },
                        {
                            "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                            "violations": [
                                {
                                    "quotaId": (
                                        "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
                                    )
                                }
                            ],
                        },
                    ]
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(LlmProviderError, match="provider_daily_quota_exhausted"):
            await _gemini_client(http_client, sleep=sleep).ainvoke("Explain safely")

    assert calls == 1
    sleep.assert_not_awaited()


def test_auto_provider_prefers_gemini_over_other_configured_providers():
    settings = SimpleNamespace(
        llm_provider="auto",
        gemini_api_key="gemini-key",
        gemini_model="gemini-3.6-flash",
        agentrouter_api_key="router-key",
        agentrouter_model="claude-test",
        openai_api_key="openai-key",
    )

    assert resolve_llm_provider(settings) == "gemini"
