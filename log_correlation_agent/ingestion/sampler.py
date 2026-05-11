from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

from log_correlation_agent.timeline.schema import LogEvent


@dataclass(slots=True)
class AdaptiveSampler:
    threshold: int = 100
    window_sec: int = 60
    keep_every: int = 20
    _seen: dict[tuple[str, str, str], deque[float]] = field(
        default_factory=lambda: defaultdict(deque)
    )
    _dropped: dict[tuple[str, str, str], int] = field(default_factory=lambda: defaultdict(int))

    def should_keep(self, event: LogEvent, now: float | None = None) -> bool:
        if event.level in {"ERROR", "FATAL"} or event.trace_id:
            return True
        current = now if now is not None else time.time()
        key = (event.service, event.level, event.event_signature)
        bucket = self._seen[key]
        while bucket and bucket[0] < current - self.window_sec:
            bucket.popleft()
        bucket.append(current)
        if event.level not in {"INFO", "DEBUG"} or len(bucket) <= self.threshold:
            return True
        self._dropped[key] += 1
        if self._dropped[key] % self.keep_every == 0:
            event.message_preview = f"{event.message_preview} (x{self._dropped[key]} in last 60s)"
            self._dropped[key] = 0
            return True
        return False
