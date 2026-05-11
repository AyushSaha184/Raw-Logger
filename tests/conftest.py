from __future__ import annotations

import time

import pytest

from log_correlation_agent.ingestion.fingerprint import event_signature
from log_correlation_agent.timeline.buffer import connect, insert_event
from log_correlation_agent.timeline.schema import LogEvent


@pytest.fixture
def in_memory_db():
    conn = connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def sample_event() -> LogEvent:
    now = time.time()
    return LogEvent.create(
        service="api",
        level="ERROR",
        message="HTTP 500 database connection failed",
        source_file="api.log",
        observed_at=now,
        ingest_ts=now,
        event_ts=now,
        effective_ts=now,
        event_signature=event_signature("HTTP 500 database connection failed"),
    )


@pytest.fixture
def sample_state(in_memory_db):
    return {
        "timeline_db": in_memory_db,
        "anomaly_window_sec": 60,
        "anomaly_suppressions": {},
        "heartbeat_state": {},
        "log_files": [{"service_name": "api"}],
    }


@pytest.fixture
def populated_db(in_memory_db, sample_event):
    insert_event(in_memory_db, sample_event)
    return in_memory_db
