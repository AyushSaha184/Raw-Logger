from __future__ import annotations

import sqlite3
from queue import Queue
from typing import Any, TypedDict


class LogCorrelationState(TypedDict, total=False):
    log_files: list[dict[str, Any]]
    retention_minutes: int
    anomaly_window_sec: int
    correlation_window_sec: int
    max_events_for_llm: int
    ingestion_queues: dict[str, Queue[Any]]
    last_file_state: dict[str, dict[str, Any]]
    clock_skew_by_service: dict[str, float]
    timeline_db: sqlite3.Connection
    total_events_ingested: int
    pattern_learning_cache: dict[str, Any]
    active_anomalies: list[dict[str, Any]]
    anomaly_history: list[dict[str, Any]]
    anomaly_suppressions: dict[str, float]
    incident_clusters: list[dict[str, Any]]
    heartbeat_state: dict[str, dict[str, float]]
    user_query: str | None
    query_intent: str | None
    query_time_anchor: float | None
    query_services: list[str]
    previous_windowed_events: list[dict[str, Any]]
    previous_query_anchor: float | None
    windowed_events: list[dict[str, Any]]
    raw_windowed_events: list[dict[str, Any]]
    llm_response: str | None
    causal_confidence: float | None
    evidence_types: list[str]
    used_llm: bool
    formatted_response: str | None
    alert_to_surface: dict[str, Any] | None
    current_incident_cluster: dict[str, Any] | None
