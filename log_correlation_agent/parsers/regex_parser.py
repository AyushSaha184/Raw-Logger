from __future__ import annotations

import re
import time
from dataclasses import dataclass

from log_correlation_agent.ingestion.fingerprint import event_signature
from log_correlation_agent.normalization.timestamp import TimestampNormalizer
from log_correlation_agent.timeline.schema import LogEvent

LEVEL_RE = re.compile(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b", re.IGNORECASE)
ISO_TEXT_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2})?)\s+(?P<rest>.*)$"
)
NGINX_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<ts>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) [^"]+" (?P<status>\d{3}) (?P<size>\S+)'
)
APACHE_RE = NGINX_RE
SYSLOG_RE = re.compile(
    r"^(?P<mon>[A-Z][a-z]{2})\s+(?P<day>\d{1,2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<host>\S+) (?P<proc>[^:]+): (?P<msg>.*)$"
)


@dataclass(frozen=True, slots=True)
class RegexPattern:
    name: str
    regex: re.Pattern[str]


def compile_safe(pattern: str) -> re.Pattern[str]:
    if not pattern.startswith("^"):
        raise ValueError("regex patterns must be anchored")
    if re.search(r"\([^)]*[+*][^)]*\)[+*]", pattern):
        raise ValueError("nested wildcard regex patterns are not allowed")
    return re.compile(pattern)


def _level_from_text(text: str) -> str:
    match = LEVEL_RE.search(text)
    if match is None:
        return "UNKNOWN"
    level = match.group(1).upper()
    return "WARN" if level == "WARNING" else "FATAL" if level == "CRITICAL" else level


def parse_regex_line(
    line: str,
    *,
    service: str,
    source_file: str = "",
    format_hint: str = "auto",
    normalizer: TimestampNormalizer | None = None,
) -> LogEvent | None:
    parser = normalizer or TimestampNormalizer()
    observed = time.time()
    extra: dict[str, str] = {}
    level = _level_from_text(line)
    message = line
    ts_source = line

    nginx_match = NGINX_RE.match(line) if format_hint in {"auto", "nginx", "apache"} else None
    if nginx_match:
        extra = nginx_match.groupdict()
        status = int(extra["status"])
        level = "ERROR" if status >= 500 else "WARN" if status >= 400 else "INFO"
        message = f"{extra['method']} {extra['path']} {status}"
        ts_source = extra["ts"]
    else:
        iso_match = ISO_TEXT_RE.match(line)
        if iso_match:
            message = iso_match.group("rest")
            ts_source = iso_match.group("ts")

    event_ts, confidence = parser.parse_timestamp(ts_source, observed)
    ingest = time.time()
    parser.observe(service, event_ts, observed)
    effective = parser.compute_effective_ts(event_ts, observed, ingest, service, confidence)
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
        extra=extra,
        event_signature=event_signature(message),
    )
