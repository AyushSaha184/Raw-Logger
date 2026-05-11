from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from log_correlation_agent.watcher.rotation import (
    detect_rotation,
    fingerprint_lines,
    skip_replayed_lines,
)


def read_new_lines(path: Path, state: dict[str, Any]) -> list[str]:
    decision = detect_rotation(path, state)
    if decision.inode is None:
        state["missing_since"] = state.get("missing_since") or time.time()
        return []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(decision.offset)
        text = handle.read()
        state["offset"] = handle.tell()
    state["inode"] = decision.inode
    lines = text.splitlines()
    if decision.rotated or decision.truncated or decision.offset == 0:
        lines = skip_replayed_lines(lines, state.get("fingerprint_last_line"))
    if lines:
        state["fingerprint_last_line"] = fingerprint_lines(lines)
        state["last_event_ts"] = time.time()
    return lines
