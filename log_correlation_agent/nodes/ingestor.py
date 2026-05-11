from __future__ import annotations

from log_correlation_agent.state import LogCorrelationState


def ingestor_node(state: LogCorrelationState) -> LogCorrelationState:
    state["total_events_ingested"] = int(state.get("total_events_ingested", 0))
    return state
