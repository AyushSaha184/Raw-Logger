from __future__ import annotations

import sqlite3
from typing import Any

from log_correlation_agent.nodes.correlation_engine import correlation_engine_node
from log_correlation_agent.nodes.heuristic_reducer import heuristic_reducer_node
from log_correlation_agent.nodes.query_router import route_query
from log_correlation_agent.nodes.response_formatter import response_formatter_node
from log_correlation_agent.state import LogCorrelationState


def build_graph() -> Any | None:
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        return None
    graph = StateGraph(LogCorrelationState)
    graph.add_node("query_router", route_query)
    graph.add_node("correlation_engine", correlation_engine_node)
    graph.add_node("heuristic_reducer", heuristic_reducer_node)
    graph.add_node("response_formatter", response_formatter_node)
    graph.set_entry_point("query_router")
    graph.add_edge("query_router", "correlation_engine")
    graph.add_edge("correlation_engine", "heuristic_reducer")
    graph.add_edge("heuristic_reducer", "response_formatter")
    graph.add_edge("response_formatter", END)
    return graph.compile()


def run_query(
    conn: sqlite3.Connection,
    query: str,
    *,
    no_llm: bool = True,
    max_events: int = 200,
    correlation_window_sec: int = 120,
) -> str:
    state: LogCorrelationState = {
        "timeline_db": conn,
        "user_query": query,
        "correlation_window_sec": correlation_window_sec,
        "max_events_for_llm": max_events,
        "log_files": [],
        "used_llm": not no_llm,
    }
    if not no_llm:
        graph = build_graph()
        if graph is not None:
            try:
                result = graph.invoke(state)
                return str(result.get("formatted_response") or "")
            except Exception:
                pass
    for node in (
        route_query,
        correlation_engine_node,
        heuristic_reducer_node,
        response_formatter_node,
    ):
        state = node(state)
    return str(state.get("formatted_response") or "")
