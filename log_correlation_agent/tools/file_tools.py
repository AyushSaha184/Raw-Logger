from __future__ import annotations

from collections import deque
from pathlib import Path


def tail_lines(path: str, limit: int) -> list[str]:
    with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
        return list(deque(handle, maxlen=limit))
