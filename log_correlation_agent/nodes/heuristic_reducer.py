from __future__ import annotations

from typing import Any

from log_correlation_agent.state import LogCorrelationState


def reduce_events(events: list[dict[str, Any]], *, max_events: int = 25) -> list[dict[str, Any]]:
    if len(events) <= max_events:
        return events
    kept: list[dict[str, Any]] = []
    seen_signatures: set[tuple[str, str, str]] = set()
    for event in events:
        if event.get("level") in {"ERROR", "FATAL"} or event.get("trace_id"):
            kept.append(event)
            continue
        key = (
            str(event.get("service")),
            str(event.get("level")),
            str(event.get("event_signature")),
        )
        if key not in seen_signatures:
            kept.append(event)
            seen_signatures.add(key)
    if len(kept) > max_events:
        kept = kept[:max_events]
    if not kept and events:
        kept.append(events[0])
    while len(kept) < min(max_events, len(events)):
        candidate = events[len(kept) * max(1, len(events) // max_events)]
        if candidate not in kept:
            kept.append(candidate)
        else:
            break
    return sorted(kept[:max_events], key=lambda row: float(row.get("effective_ts", 0)))


def heuristic_reducer_node(state: LogCorrelationState) -> LogCorrelationState:
    state["windowed_events"] = reduce_events(state.get("raw_windowed_events", []), max_events=25)
    return state
