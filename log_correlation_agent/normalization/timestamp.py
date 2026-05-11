from __future__ import annotations

import re
import statistics
import time
from collections import defaultdict, deque
from datetime import UTC

try:
    from dateutil import parser as date_parser  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    date_parser = None


TIMESTAMP_RE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
)


class TimestampNormalizer:
    def __init__(self) -> None:
        self.clock_skew_by_service: dict[str, float] = {}
        self._samples: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=20))

    def parse_timestamp(self, line: str, observed_at: float | None = None) -> tuple[float, float]:
        observed = observed_at if observed_at is not None else time.time()
        match = TIMESTAMP_RE.search(line)
        if match is None or date_parser is None:
            return observed, 0.1
        try:
            dt = date_parser.parse(match.group("ts"))
        except (ValueError, OverflowError, TypeError):
            return observed, 0.1
        confidence = 1.0
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
            confidence *= 0.8
        return dt.astimezone(UTC).timestamp(), confidence

    def observe(self, service: str, event_ts: float, observed_at: float) -> None:
        raw_delay = observed_at - event_ts
        if abs(raw_delay) >= 300:
            return
        samples = self._samples[service]
        samples.append(raw_delay)
        if len(samples) >= 10:
            self.clock_skew_by_service[service] = float(statistics.median(samples))

    def compute_effective_ts(
        self,
        event_ts: float,
        observed_at: float,
        ingest_ts: float,
        service: str,
        ts_confidence: float,
    ) -> float:
        del ingest_ts
        skew = self.clock_skew_by_service.get(service, 0.0)
        corrected = event_ts - skew
        return (corrected * ts_confidence) + (observed_at * (1 - ts_confidence))


def utc_timestamp(value: str) -> float:
    if date_parser is None:
        raise RuntimeError("python-dateutil is required for timestamp parsing")
    dt = date_parser.parse(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return float(dt.astimezone(UTC).timestamp())
