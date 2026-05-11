from __future__ import annotations

from log_correlation_agent.nodes.alert_correlator import correlate_alerts
from log_correlation_agent.state import LogCorrelationState


def alert_manager_node(state: LogCorrelationState) -> LogCorrelationState:
    clusters = correlate_alerts(state.get("active_anomalies", []))
    state["incident_clusters"] = clusters
    state["current_incident_cluster"] = clusters[0] if clusters else None
    state["alert_to_surface"] = clusters[0]["root_anomaly"] if clusters else None
    return state
