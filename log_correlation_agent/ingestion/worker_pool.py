from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from os import cpu_count
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


@dataclass(slots=True)
class ParserWorkerPool:
    max_workers: int | None = None

    def __post_init__(self) -> None:
        if self.max_workers is None:
            self.max_workers = max(1, (cpu_count() or 2) - 1)

    def map(self, fn: Callable[[T], R], items: Iterable[T]) -> list[R]:
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(fn, items))
