from __future__ import annotations

from log_correlation_agent.state import LogCorrelationState


def response_formatter_node(state: LogCorrelationState) -> LogCorrelationState:
    intent = state.get("query_intent")
    events = state.get("windowed_events", [])
    if intent == "count":
        counts: dict[str, int] = {}
        for event in events:
            level = str(event.get("level", "UNKNOWN"))
            counts[level] = counts.get(level, 0) + 1
        state["formatted_response"] = (
            "\n".join(f"{level}: {count}" for level, count in sorted(counts.items()))
            or "No events found."
        )
        return state
    if not events:
        state["formatted_response"] = "No matching events found."
        return state
    lines = []
    for event in events[:25]:
        lines.append(
            f"{event.get('effective_ts'):.3f} [{event.get('service')}] [{event.get('level')}] {event.get('message_preview')}"
        )
    state["formatted_response"] = "\n".join(lines)
    return state
