from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from log_correlation_agent.watcher.tail import read_new_lines


@dataclass(slots=True)
class FileWatcherManager:
    paths: list[Path]
    on_lines: Callable[[Path, list[str]], None]
    last_file_state: dict[str, dict[str, object]] = field(default_factory=dict)

    def poll_once(self) -> None:
        for path in self.paths:
            state = self.last_file_state.setdefault(str(path), {})
            lines = read_new_lines(path, state)
            if lines:
                self.on_lines(path, lines)
