from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import import_module
from typing import Any, cast

from tenacity import retry, stop_after_attempt, wait_exponential

CONFIDENCE_RE = re.compile(r"<CONFIDENCE>(?P<json>.*?)</CONFIDENCE>", re.DOTALL)
FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


@dataclass(slots=True)
class GeminiAdapter:
    api_key: str | None = None
    flash_model: str = "gemini-1.5-flash"
    pro_model: str = "gemini-1.5-pro"
    no_llm: bool = False

    def __post_init__(self) -> None:
        self.no_llm = self.no_llm or os.getenv("LOG_CORR_NO_LLM", "").lower() == "true"
        self.api_key = self.api_key or os.getenv("GEMINI_API_KEY")

    def _client(self, model: str) -> Any:
        if self.no_llm:
            raise RuntimeError("LLM calls are disabled")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for LLM calls")
        genai = import_module("google.generativeai")
        genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(model)

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        if self.no_llm:
            raise RuntimeError("LLM calls are disabled")
        return self._complete_with_retry(prompt, model=model)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _complete_with_retry(self, prompt: str, *, model: str | None = None) -> str:
        client = self._client(model or self.flash_model)
        response = client.generate_content(prompt)
        return str(getattr(response, "text", ""))

    def complete_json(self, prompt: str, *, model: str | None = None) -> dict[str, Any]:
        return cast(
            dict[str, Any], json.loads(strip_json_fences(self.complete(prompt, model=model)))
        )

    def complete_streaming(self, chunks: Iterable[Any]) -> str:
        return "".join(str(getattr(chunk, "text", chunk)) for chunk in chunks)


def strip_json_fences(text: str) -> str:
    return FENCE_RE.sub("", text.strip()).strip()


def extract_confidence(text: str) -> dict[str, Any]:
    match = CONFIDENCE_RE.search(text)
    if match is None:
        return {"causal_confidence": None, "evidence_types": []}
    try:
        return cast(dict[str, Any], json.loads(match.group("json")))
    except json.JSONDecodeError:
        return {"causal_confidence": None, "evidence_types": []}
