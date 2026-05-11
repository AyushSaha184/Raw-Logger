from __future__ import annotations

import hashlib
import time
import uuid
import zlib
from dataclasses import asdict, dataclass, field
from typing import Any

MAX_MESSAGE_CHARS = 500
MAX_PREVIEW_CHARS = 120


def _compress(raw: str) -> bytes:
    return zlib.compress(raw.encode("utf-8", errors="replace"))


@dataclass(slots=True)
class LogEvent:
    event_id: str
    observed_at: float
    ingest_ts: float
    event_ts: float
    effective_ts: float
    ts_confidence: float
    service: str
    level: str
    message: str
    message_preview: str
    payload_hash: str
    raw_line_compressed: bytes
    trace_id: str | None
    source_file: str
    extra: dict[str, Any]
    event_signature: str
    is_continuation: bool = False
    composite_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        service: str,
        level: str,
        message: str,
        raw_line: str | None = None,
        source_file: str = "",
        observed_at: float | None = None,
        ingest_ts: float | None = None,
        event_ts: float | None = None,
        effective_ts: float | None = None,
        ts_confidence: float = 1.0,
        trace_id: str | None = None,
        extra: dict[str, Any] | None = None,
        event_signature: str = "",
        is_continuation: bool = False,
        composite_id: str | None = None,
    ) -> LogEvent:
        now = time.time()
        observed = observed_at if observed_at is not None else now
        ingest = ingest_ts if ingest_ts is not None else now
        event_time = event_ts if event_ts is not None else observed
        effective = effective_ts if effective_ts is not None else event_time
        raw = raw_line if raw_line is not None else message
        full_hash = hashlib.md5(message.encode("utf-8", errors="replace")).hexdigest()
        return cls(
            event_id=str(uuid.uuid4()),
            observed_at=observed,
            ingest_ts=ingest,
            event_ts=event_time,
            effective_ts=effective,
            ts_confidence=ts_confidence,
            service=service,
            level=level.upper(),
            message=message[:MAX_MESSAGE_CHARS],
            message_preview=message[:MAX_PREVIEW_CHARS],
            payload_hash=full_hash,
            raw_line_compressed=_compress(raw),
            trace_id=trace_id,
            source_file=source_file,
            extra=extra or {},
            event_signature=event_signature,
            is_continuation=is_continuation,
            composite_id=composite_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CompositeLogEvent:
    composite_id: str
    lines: list[LogEvent]
    service: str
    level: str
    message: str
    effective_ts: float
    trace_id: str | None
    source_file: str
    event_signature: str
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_lines(cls, lines: list[LogEvent]) -> CompositeLogEvent:
        if not lines:
            raise ValueError("CompositeLogEvent requires at least one line")
        first = lines[0]
        composite_id = first.composite_id or str(uuid.uuid4())
        for line in lines:
            line.composite_id = composite_id
            line.is_continuation = line is not first
        message = "\n".join(line.message for line in lines)
        if len(lines) > 50:
            message = "\n".join(
                [line.message for line in lines[:10]]
                + ["..."]
                + [line.message for line in lines[-5:]]
            )
        return cls(
            composite_id=composite_id,
            lines=lines,
            service=first.service,
            level=first.level,
            message=message,
            effective_ts=first.effective_ts,
            trace_id=first.trace_id,
            source_file=first.source_file,
            event_signature=first.event_signature,
        )
