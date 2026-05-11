from __future__ import annotations

import re
import time

from log_correlation_agent.state import LogCorrelationState
from log_correlation_agent.timeline.queries import find_latest_error

TIME_RE = re.compile(r"\b(?P<hour>\d{1,2}):(?P<minute>\d{2})\b")


def route_query(state: LogCorrelationState) -> LogCorrelationState:
    query = (state.get("user_query") or "").lower()
    if any(word in query for word in ("how many", "count")):
        intent = "count"
    elif any(word in query for word in ("caused", "before", "after", "why")):
        intent = "causal"
    elif any(word in query for word in ("show", "timeline", "logs")):
        intent = "timeline"
    else:
        intent = "summary"
    services = []
    for item in state.get("log_files", []):
        name = str(item.get("service_name", ""))
        if name and name.lower() in query:
            services.append(name)
    anchor = _resolve_anchor(state, query)
    state["query_intent"] = intent
    state["query_services"] = services
    state["query_time_anchor"] = anchor
    return state


def _resolve_anchor(state: LogCorrelationState, query: str) -> float | None:
    db = state.get("timeline_db")
    if ("500" in query or "error" in query) and db is not None:
        latest = find_latest_error(db)
        if latest:
            return float(latest["effective_ts"])
    match = TIME_RE.search(query)
    if not match:
        return time.time()
    now = time.localtime()
    return time.mktime(
        (
            now.tm_year,
            now.tm_mon,
            now.tm_mday,
            int(match.group("hour")),
            int(match.group("minute")),
            0,
            now.tm_wday,
            now.tm_yday,
            now.tm_isdst,
        )
    )
