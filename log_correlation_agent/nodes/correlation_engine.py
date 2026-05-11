from __future__ import annotations

import time

from log_correlation_agent.state import LogCorrelationState
from log_correlation_agent.timeline.queries import query_time_range


def correlation_engine_node(state: LogCorrelationState) -> LogCorrelationState:
    db = state["timeline_db"]
    anchor = state.get("query_time_anchor") or time.time()
    window = int(state.get("correlation_window_sec", 120))
    half = window / 2
    events = query_time_range(
        db,
        anchor - half,
        anchor + half,
        services=state.get("query_services") or None,
        limit=int(state.get("max_events_for_llm", 200)),
    )
    state["raw_windowed_events"] = events
    return state
