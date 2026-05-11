from __future__ import annotations

import time
from typing import Any

from log_correlation_agent.state import LogCorrelationState
from log_correlation_agent.timeline.queries import query_time_range


def detect_anomalies(
    state: LogCorrelationState,
    *,
    now: float | None = None,
    error_threshold: int = 10,
    auth_threshold: int = 5,
) -> list[dict[str, Any]]:
    current = now if now is not None else time.time()
    window = int(state.get("anomaly_window_sec", 60))
    db = state.get("timeline_db")
    anomalies: list[dict[str, Any]] = []
    if db is not None:
        events = query_time_range(db, current - window, current, limit=10000)
        errors = [event for event in events if event["level"] in {"ERROR", "FATAL"}]
        if len(errors) > error_threshold:
            anomalies.append(
                _anomaly("error_rate_spike", "global", current, "high", f"{len(errors)} errors")
            )
        auth = [
            event
            for event in events
            if "auth" in str(event["message_preview"]).lower()
            and event["level"] in {"WARN", "ERROR", "FATAL"}
        ]
        if len(auth) > auth_threshold:
            anomalies.append(
                _anomaly(
                    "auth_failure_cascade", "global", current, "high", f"{len(auth)} auth failures"
                )
            )
    heartbeat = state.get("heartbeat_state", {})
    for service, info in heartbeat.items():
        first_seen = float(info.get("first_seen_ts", current))
        last_seen = float(info.get("last_seen_ts", current))
        expected = float(info.get("expected_freq_sec", 5))
        if current - first_seen < 120:
            continue
        if current - last_seen > expected * float(info.get("silence_multiplier", 5.0)):
            anomalies.append(
                _anomaly("service_silent", service, current, "medium", "service heartbeat stopped")
            )
    return _apply_suppression(state, anomalies, current)


def anomaly_detector_node(state: LogCorrelationState) -> LogCorrelationState:
    anomalies = detect_anomalies(state)
    state["active_anomalies"] = anomalies
    state.setdefault("anomaly_history", []).extend(anomalies)
    return state


def _anomaly(
    kind: str, service: str, timestamp: float, severity: str, detail: str
) -> dict[str, Any]:
    return {
        "type": kind,
        "service": service,
        "timestamp": timestamp,
        "severity": severity,
        "detail": detail,
    }


def _apply_suppression(
    state: LogCorrelationState, anomalies: list[dict[str, Any]], current: float
) -> list[dict[str, Any]]:
    suppressions = state.setdefault("anomaly_suppressions", {})
    out: list[dict[str, Any]] = []
    for anomaly in anomalies:
        key = f"{anomaly['type']}:{anomaly['service']}"
        if suppressions.get(key, 0) > current:
            continue
        suppressions[key] = current + 300
        out.append(anomaly)
    return out
