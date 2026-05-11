from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FuzzyParseRequest:
    line: str
    service: str
    source_file: str
    needs_llm_parse: bool = True
