from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class RotationDecision:
    rotated: bool
    truncated: bool
    offset: int
    inode: int | None


def fingerprint_lines(lines: list[str]) -> str:
    return hashlib.md5("\n".join(lines[-3:]).encode("utf-8", errors="replace")).hexdigest()


def detect_rotation(path: Path, state: dict[str, Any]) -> RotationDecision:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return RotationDecision(
            rotated=False, truncated=False, offset=int(state.get("offset", 0)), inode=None
        )
    inode = getattr(stat, "st_ino", None)
    previous_inode = state.get("inode")
    previous_offset = int(state.get("offset", 0))
    if previous_inode is not None and inode != previous_inode:
        return RotationDecision(rotated=True, truncated=False, offset=0, inode=inode)
    if stat.st_size < previous_offset:
        return RotationDecision(rotated=False, truncated=True, offset=0, inode=inode)
    return RotationDecision(rotated=False, truncated=False, offset=previous_offset, inode=inode)


def skip_replayed_lines(lines: list[str], stored_fingerprint: str | None) -> list[str]:
    if not stored_fingerprint:
        return lines
    for idx in range(min(len(lines), 10)):
        if fingerprint_lines(lines[: idx + 1]) == stored_fingerprint:
            return lines[idx + 1 :]
    return lines
