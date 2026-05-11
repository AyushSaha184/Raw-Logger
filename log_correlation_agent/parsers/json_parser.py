from __future__ import annotations

import json
import time
from typing import Any

from log_correlation_agent.ingestion.fingerprint import event_signature
from log_correlation_agent.normalization.timestamp import TimestampNormalizer
from log_correlation_agent.timeline.schema import LogEvent


def parse_json_line(
    line: str,
    *,
    service: str,
    source_file: str = "",
    normalizer: TimestampNormalizer | None = None,
) -> LogEvent:
    data: dict[str, Any] = json.loads(line)
    observed = time.time()
    message = str(data.get("message") or data.get("msg") or data)
    level = str(data.get("level") or data.get("severity") or "INFO").upper()
    ts_value = str(data.get("timestamp") or data.get("time") or data.get("ts") or "")
    parser = normalizer or TimestampNormalizer()
    event_ts, confidence = parser.parse_timestamp(ts_value or line, observed)
    ingest = time.time()
    parser.observe(service, event_ts, observed)
    effective = parser.compute_effective_ts(event_ts, observed, ingest, service, confidence)
    trace_id = data.get("trace_id") or data.get("traceId")
    return LogEvent.create(
        service=service,
        level=level,
        message=message,
        raw_line=line,
        source_file=source_file,
        observed_at=observed,
        ingest_ts=ingest,
        event_ts=event_ts,
        effective_ts=effective,
        ts_confidence=confidence,
        trace_id=str(trace_id) if trace_id else None,
        extra=data,
        event_signature=event_signature(message),
    )
