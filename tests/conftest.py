from unittest.mock import AsyncMock

import pytest

try:
    import pytest_asyncio
    async_fixture = pytest_asyncio.fixture
except ImportError:
    async_fixture = pytest.fixture

from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture(autouse=True)
def disable_live_llm_for_unit_tests(monkeypatch):
    """Never spend provider calls merely because a developer has a local key.

    Tests that exercise the model boundary explicitly replace ``get_settings``
    again inside the test. The live-evaluation script remains provider-backed.
    """
    from src.agents.nodes import orchestration

    settings = orchestration.get_settings().model_copy(
        update={"openai_api_key": "", "agentrouter_api_key": "", "gemini_api_key": ""}
    )
    monkeypatch.setattr(orchestration, "get_settings", lambda: settings)


@async_fixture
async def client():
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_llm():
    """Mock LLM to avoid calling OpenAI during tests.

    Usage in test:
        def test_something(mock_llm):
            # LLM calls will return mock response instead of hitting OpenAI
            ...
    """
    mock = AsyncMock()
    mock.ainvoke.return_value = AsyncMock(content="Mocked LLM response")
    return mock
