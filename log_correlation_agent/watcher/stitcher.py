from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field

TIMESTAMP_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}")
ERROR_RE = re.compile(r"\b(ERROR|FATAL|CRITICAL)\b", re.IGNORECASE)
CONTINUATION_PATTERNS = [
    re.compile(r"^\s+"),
    re.compile(r"^\s+at [A-Za-z]"),
    re.compile(r'^\s+File "'),
    re.compile(r"^\s+Traceback"),
    re.compile(r"^\s+at (?:new )?[A-Za-z]"),
    re.compile(r"^Caused by:"),
    re.compile(r"^\.\.\. \d+ more"),
]


@dataclass(slots=True)
class StitchedRecord:
    lines: list[str]
    composite_id: str | None = None


@dataclass(slots=True)
class _Pending:
    lines: list[str] = field(default_factory=list)
    started_at: float = 0.0
    last_at: float = 0.0
    composite_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class LogStitcher:
    def __init__(self, *, timeout_sec: float = 3.0, max_lines: int = 200) -> None:
        self.timeout_sec = timeout_sec
        self.max_lines = max_lines
        self._pending: dict[str, _Pending] = {}

    def add_line(
        self, source_file: str, line: str, *, now: float | None = None
    ) -> list[StitchedRecord]:
        current = now if now is not None else time.time()
        pending = self._pending.get(source_file)
        out: list[StitchedRecord] = []
        is_cont = self._is_continuation(
            line, pending.lines[-1] if pending and pending.lines else None
        )
        if pending is None:
            self._pending[source_file] = _Pending(lines=[line], started_at=current, last_at=current)
            return out
        if is_cont:
            pending.lines.append(line)
            pending.last_at = current
            if len(pending.lines) >= self.max_lines:
                record = self._flush(source_file)
                if record is not None:
                    out.append(record)
            return out
        record = self._flush(source_file)
        if record is not None:
            out.append(record)
        self._pending[source_file] = _Pending(lines=[line], started_at=current, last_at=current)
        return out

    def flush_expired(self, *, now: float | None = None) -> list[StitchedRecord]:
        current = now if now is not None else time.time()
        out: list[StitchedRecord] = []
        for source_file, pending in list(self._pending.items()):
            if current - pending.last_at >= self.timeout_sec:
                record = self._flush(source_file)
                if record:
                    out.append(record)
        return out

    def flush_all(self) -> list[StitchedRecord]:
        out: list[StitchedRecord] = []
        for source_file in list(self._pending):
            record = self._flush(source_file)
            if record:
                out.append(record)
        return out

    def _flush(self, source_file: str) -> StitchedRecord | None:
        pending = self._pending.pop(source_file, None)
        if pending is None:
            return None
        composite_id = pending.composite_id if len(pending.lines) > 1 else None
        return StitchedRecord(lines=pending.lines, composite_id=composite_id)

    def _is_continuation(self, line: str, previous: str | None) -> bool:
        if any(pattern.search(line) for pattern in CONTINUATION_PATTERNS):
            return True
        return bool(previous and ERROR_RE.search(previous) and not TIMESTAMP_PREFIX_RE.search(line))
