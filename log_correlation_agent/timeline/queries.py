from __future__ import annotations

import sqlite3
from typing import Any


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def query_time_range(
    conn: sqlite3.Connection,
    start_ts: float,
    end_ts: float,
    *,
    services: list[str] | None = None,
    levels: list[str] | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    clauses = ["effective_ts BETWEEN ? AND ?"]
    params: list[Any] = [start_ts, end_ts]
    if services:
        clauses.append(f"service IN ({','.join('?' for _ in services)})")
        params.extend(services)
    if levels:
        clauses.append(f"level IN ({','.join('?' for _ in levels)})")
        params.extend(levels)
    params.append(limit)
    rows = conn.execute(
        f"SELECT * FROM events WHERE {' AND '.join(clauses)} ORDER BY effective_ts ASC LIMIT ?",
        params,
    ).fetchall()
    return rows_to_dicts(rows)


def count_by_level(conn: sqlite3.Connection, start_ts: float, end_ts: float) -> dict[str, int]:
    rows = conn.execute(
        "SELECT level, COUNT(*) AS count FROM events WHERE effective_ts BETWEEN ? AND ? GROUP BY level",
        (start_ts, end_ts),
    ).fetchall()
    return {str(row["level"]): int(row["count"]) for row in rows}


def find_latest_error(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM events WHERE level IN ('ERROR', 'FATAL') ORDER BY effective_ts DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def query_service(
    conn: sqlite3.Connection, service: str, *, limit: int = 100
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM events WHERE service = ? ORDER BY effective_ts DESC LIMIT ?",
        (service, limit),
    ).fetchall()
    return rows_to_dicts(rows)
