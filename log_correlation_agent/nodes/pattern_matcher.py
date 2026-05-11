from __future__ import annotations

from log_correlation_agent.state import LogCorrelationState


def pattern_matcher_node(state: LogCorrelationState) -> LogCorrelationState:
    state["used_llm"] = False
    return state
