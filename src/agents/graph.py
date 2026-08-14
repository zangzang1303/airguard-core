from __future__ import annotations

from functools import partial
from typing import Any

from langgraph.graph import END, StateGraph

from src.agents.nodes.orchestration import compose_node, execute_tools_node, generate_explanation_node, route_after_intent, route_node, trace_node
from src.agents.nodes.proposal_workflow import run_proposal_workflow
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
    graph.add_node("create_proposal", partial(create_proposal_node, tool_client=tool_client))
    graph.add_node("compose", compose_node)
    graph.add_node("generate_explanation", generate_explanation_node)
    graph.add_node("trace", trace_node)
    graph.set_entry_point("route")
    graph.add_conditional_edges("route", route_after_intent)
    graph.add_edge("execute_tools", "compose")
    graph.add_edge("create_proposal", "compose")
    graph.add_edge("compose", "generate_explanation")
    graph.add_edge("generate_explanation", "trace")
    graph.add_edge("trace", END)
    return graph.compile()


async def create_proposal_node(state: AgentState, *, tool_client: Any) -> dict[str, Any]:
    route = state["route"]
    station_id = route.get("tool_arguments", [{}])[0].get("station_id")
    result = await run_proposal_workflow(
        station_id=station_id or "",
        user_id=state.get("user_id") or "",
        request_id=state["request_id"],
        tool_client=tool_client,
    )
    return {
        "tool_results": result.tool_results,
        "tool_traces": result.tool_traces,
        "used_tools": [trace["tool_name"] for trace in result.tool_traces],
        "proposal_id": result.proposal_id,
        "proposal_reason_code": result.reason_code,
        "outcome": result.outcome,
    }


agent = build_graph()
