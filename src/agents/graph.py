from __future__ import annotations

from functools import partial
from typing import Any

from langgraph.graph import END, StateGraph

from src.agents.nodes.orchestration import compose_node, execute_tools_node, route_after_intent, route_node, trace_node
from src.agents.state import AgentState
from src.agents.tools.backend_client import BackendToolClient
from src.config import get_settings


def build_graph(tool_client: Any | None = None):
    """Build the grounded graph; tests inject the fake adapter and need no DB/LLM."""
    if tool_client is None:
        settings = get_settings()
        tool_client = BackendToolClient(
            settings.agent_backend_base_url,
            timeout_seconds=settings.agent_tool_timeout_seconds,
            max_retries=settings.agent_tool_max_retries,
        )

    graph = StateGraph(AgentState)
    graph.add_node("route", route_node)
    graph.add_node("execute_tools", partial(execute_tools_node, tool_client=tool_client))
    graph.add_node("compose", compose_node)
    graph.add_node("trace", trace_node)
    graph.set_entry_point("route")
    graph.add_conditional_edges("route", route_after_intent)
    graph.add_edge("execute_tools", "compose")
    graph.add_edge("compose", "trace")
    graph.add_edge("trace", END)
    return graph.compile()


agent = build_graph()
