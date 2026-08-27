from pathlib import Path

FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend" / "src"
CLIENT_SOURCE = (FRONTEND_ROOT / "api" / "client.ts").read_text(encoding="utf-8")
APP_SOURCE = (FRONTEND_ROOT / "App.tsx").read_text(encoding="utf-8")


def test_agent_chat_uses_one_post_contract_without_polling_or_fake_streaming() -> None:
    start = CLIENT_SOURCE.index("sendAgentMessage: async")
    end = CLIENT_SOURCE.index("getAdminUsers: async", start)
    agent_transport = CLIENT_SOURCE[start:end]

    assert 'apiFetch<any>("/api/v1/agent/chat"' in agent_transport
    assert 'method: "POST"' in agent_transport
    assert "setInterval" not in agent_transport
    assert "EventSource" not in agent_transport
    assert "WebSocket" not in agent_transport


def test_dashboard_polling_remains_separate_from_agent_chat() -> None:
    assert "const interval = setInterval" in APP_SOURCE
    assert "refreshData" in APP_SOURCE
