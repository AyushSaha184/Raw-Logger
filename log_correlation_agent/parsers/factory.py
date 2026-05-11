from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

from log_correlation_agent.ingestion.fingerprint import event_signature
from log_correlation_agent.normalization.timestamp import TimestampNormalizer
from log_correlation_agent.parsers.json_parser import parse_json_line
from log_correlation_agent.parsers.regex_parser import parse_regex_line
from log_correlation_agent.timeline.schema import LogEvent


class PatternLearningCache:
    def __init__(self, max_size: int = 500) -> None:
        self.max_size = max_size
        self._items: OrderedDict[str, str] = OrderedDict()

    def get(self, key: str) -> str | None:
        value = self._items.get(key)
        if value is not None:
            self._items.move_to_end(key)
        return value

    def set(self, key: str, value: str) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        while len(self._items) > self.max_size:
            self._items.popitem(last=False)

    def save(self, path: str) -> None:
        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self._items), encoding="utf-8")

    @classmethod
    def load(cls, path: str, max_size: int = 500) -> PatternLearningCache:
        cache = cls(max_size=max_size)
        target = Path(path).expanduser()
        if not target.exists():
            return cache
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return cache
        for key, value in data.items():
            cache.set(str(key), str(value))
        return cache


class ParserFactory:
    def __init__(
        self,
        *,
        normalizer: TimestampNormalizer | None = None,
        pattern_cache: PatternLearningCache | None = None,
    ) -> None:
        self.normalizer = normalizer or TimestampNormalizer()
        self.pattern_cache = pattern_cache or PatternLearningCache()

    def parse(
        self,
        line: str,
        *,
        service: str,
        source_file: str = "",
        format_hint: str = "auto",
    ) -> LogEvent:
        cache_key = event_signature(line)
        if self.pattern_cache.get(cache_key):
            return parse_regex_line(
                line,
                service=service,
                source_file=source_file,
                format_hint="plaintext",
                normalizer=self.normalizer,
            )  # type: ignore[return-value]

        stripped = line.strip()
        if format_hint in {"auto", "json"} and stripped.startswith("{"):
            try:
                return parse_json_line(
                    line,
                    service=service,
                    source_file=source_file,
                    normalizer=self.normalizer,
                )
            except json.JSONDecodeError:
                if format_hint == "json":
                    raise

        parsed = parse_regex_line(
            line,
            service=service,
            source_file=source_file,
            format_hint=format_hint,
            normalizer=self.normalizer,
        )
        if parsed is None:
            return self._unknown_event(line, service=service, source_file=source_file)
        if (
            parsed.level == "UNKNOWN"
            and self.normalizer.parse_timestamp(line, parsed.observed_at)[1] == 0.1
        ):
            parsed.extra["needs_llm_parse"] = True
        return parsed

    def _unknown_event(self, line: str, *, service: str, source_file: str) -> LogEvent:
        event = parse_regex_line(
            line,
            service=service,
            source_file=source_file,
            format_hint="plaintext",
            normalizer=self.normalizer,
        )
        if event is None:
            raise RuntimeError("plaintext parser failed")
        event.extra["needs_llm_parse"] = True
        return event
