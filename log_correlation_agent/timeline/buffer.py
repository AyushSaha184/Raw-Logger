from __future__ import annotations

import json
import queue
import sqlite3
import threading
import time
from pathlib import Path

from log_correlation_agent.timeline.schema import LogEvent

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-32000;
PRAGMA temp_store=MEMORY;

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    observed_at REAL NOT NULL,
    ingest_ts REAL NOT NULL,
    event_ts REAL NOT NULL,
    effective_ts REAL NOT NULL,
    ts_confidence REAL NOT NULL DEFAULT 1.0,
    service TEXT NOT NULL,
    level TEXT NOT NULL,
    message_preview TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    raw_line_compressed BLOB,
    trace_id TEXT,
    source_file TEXT NOT NULL,
    event_signature TEXT NOT NULL,
    composite_id TEXT,
    extra TEXT
);

CREATE INDEX IF NOT EXISTS idx_effective_ts ON events(effective_ts);
CREATE INDEX IF NOT EXISTS idx_service ON events(service);
CREATE INDEX IF NOT EXISTS idx_level ON events(level);
CREATE INDEX IF NOT EXISTS idx_trace_id ON events(trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_signature ON events(event_signature);
CREATE INDEX IF NOT EXISTS idx_level_ts ON events(level, effective_ts);
"""


def connect(path: str = ":memory:") -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


class TimelineBuffer:
    def __init__(self, path: str = ":memory:", *, retention_minutes: int = 120) -> None:
        self.conn = connect(path)
        self.retention_minutes = retention_minutes
        self._writes: queue.Queue[LogEvent | None] = queue.Queue()
        self._stop = threading.Event()
        self._writer = threading.Thread(
            target=self._writer_loop, name="timeline-writer", daemon=True
        )
        self._writer.start()

    def close(self) -> None:
        self._writes.put(None)
        self._writer.join(timeout=2)
        self.conn.close()

    def insert(self, event: LogEvent) -> None:
        self._writes.put(event)

    def insert_sync(self, event: LogEvent) -> None:
        insert_event(self.conn, event)

    def cleanup_retention(self, now: float | None = None) -> int:
        cutoff = (now if now is not None else time.time()) - (self.retention_minutes * 60)
        cur = self.conn.execute("DELETE FROM events WHERE effective_ts < ?", (cutoff,))
        self.conn.commit()
        return cur.rowcount

    def _writer_loop(self) -> None:
        while not self._stop.is_set():
            event = self._writes.get()
            if event is None:
                return
            insert_event(self.conn, event)


def insert_event(conn: sqlite3.Connection, event: LogEvent) -> None:
    duplicate = conn.execute(
        """
        SELECT event_id, extra FROM events
        WHERE service = ? AND payload_hash = ? AND effective_ts BETWEEN ? AND ?
        ORDER BY effective_ts DESC LIMIT 1
        """,
        (event.service, event.payload_hash, event.effective_ts - 5, event.effective_ts + 5),
    ).fetchone()
    if duplicate is not None:
        extra = json.loads(duplicate["extra"] or "{}")
        extra["repeat_count"] = int(extra.get("repeat_count", 1)) + 1
        conn.execute(
            "UPDATE events SET extra = ? WHERE event_id = ?",
            (json.dumps(extra), duplicate["event_id"]),
        )
        conn.commit()
        return
    conn.execute(
        """
        INSERT INTO events (
            event_id, observed_at, ingest_ts, event_ts, effective_ts, ts_confidence,
            service, level, message_preview, payload_hash, raw_line_compressed, trace_id,
            source_file, event_signature, composite_id, extra
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.event_id,
            event.observed_at,
            event.ingest_ts,
            event.event_ts,
            event.effective_ts,
            event.ts_confidence,
            event.service,
            event.level,
            event.message_preview,
            event.payload_hash,
            event.raw_line_compressed,
            event.trace_id,
            event.source_file,
            event.event_signature,
            event.composite_id,
            json.dumps(event.extra),
        ),
    )
    conn.commit()
