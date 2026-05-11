from __future__ import annotations

import queue
import time
from dataclasses import dataclass, field
from typing import Any

LEVELS = ("ERROR", "WARN", "INFO", "DEBUG")


@dataclass(slots=True)
class IngestionQueues:
    error_size: int = 10000
    warn_size: int = 10000
    info_size: int = 50000
    debug_size: int = 50000
    queues: dict[str, queue.Queue[dict[str, Any]]] = field(init=False)
    debug_drop_active: bool = False
    last_debug_warning_ts: float = 0.0

    def __post_init__(self) -> None:
        self.queues = {
            "ERROR": queue.Queue(maxsize=self.error_size),
            "WARN": queue.Queue(maxsize=self.warn_size),
            "INFO": queue.Queue(maxsize=self.info_size),
            "DEBUG": queue.Queue(maxsize=self.debug_size),
        }

    def put(self, item: dict[str, Any], *, block_for_errors: bool = True) -> bool:
        level = str(item.get("level", "INFO")).upper()
        if level not in self.queues:
            level = "INFO"
        q = self.queues[level]
        if level == "DEBUG" and self.capacity_pct("DEBUG") >= 50:
            self.debug_drop_active = True
            self.last_debug_warning_ts = time.time()
            return False
        try:
            q.put(item, block=level == "ERROR" and block_for_errors, timeout=0.25)
        except queue.Full:
            return False
        return True

    def capacity_pct(self, level: str) -> float:
        q = self.queues[level]
        return (q.qsize() / q.maxsize) * 100

    def info_sampling_active(self) -> bool:
        return self.capacity_pct("INFO") >= 80

    def drain(self, *, info_limit: int = 1000, debug_limit: int = 250) -> list[dict[str, Any]]:
        drained: list[dict[str, Any]] = []
        for level in ("ERROR", "WARN"):
            q = self.queues[level]
            while not q.empty():
                drained.append(q.get_nowait())
        for level, limit in (("INFO", info_limit), ("DEBUG", debug_limit)):
            q = self.queues[level]
            for _ in range(limit):
                if q.empty():
                    break
                drained.append(q.get_nowait())
        return drained
