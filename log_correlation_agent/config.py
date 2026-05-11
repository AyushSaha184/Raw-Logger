from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import toml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    toml = None


@dataclass(slots=True)
class LogFileConfig:
    path: str
    service_name: str
    format_hint: str = "auto"
    expected_log_freq_sec: int = 5


@dataclass(slots=True)
class AppConfig:
    log_files: list[LogFileConfig] = field(default_factory=list)
    retention_minutes: int = 120
    startup_tail_lines: int = 100
    correlation_window_sec: int = 120
    max_events_for_llm: int = 200
    anomaly_window_sec: int = 60
    error_rate_threshold: int = 10
    auth_failure_threshold: int = 5
    latency_threshold_ms: int = 2000
    silence_multiplier: float = 5.0
    regex_timeout_ms: int = 50
    backpressure_info_pct: int = 80
    backpressure_debug_pct: int = 50
    pattern_cache_path: str = "~/.logcorr/pattern_cache.json"
    pattern_cache_max_size: int = 500
    retry_attempts: int = 3
    retry_wait: float = 2.0
    gemini_api_key: str | None = None
    pro_model: str = "gemini-1.5-pro"
    flash_model: str = "gemini-1.5-flash"
    no_llm: bool = False


def _coerce_log_files(items: list[dict[str, Any]]) -> list[LogFileConfig]:
    return [
        LogFileConfig(
            path=str(item["path"]),
            service_name=str(item.get("service_name") or Path(str(item["path"])).stem),
            format_hint=str(item.get("format_hint", "auto")),
            expected_log_freq_sec=int(item.get("expected_log_freq_sec", 5)),
        )
        for item in items
    ]


def load_config(path: str | None = None, *, no_llm: bool = False) -> AppConfig:
    data: dict[str, Any] = {}
    candidates = [Path(path)] if path else [Path(".logcorr.toml"), Path.home() / ".logcorr.toml"]
    for candidate in candidates:
        if candidate.exists():
            if toml is None:
                raise RuntimeError("toml package is required to load config files")
            data = toml.load(candidate)
            break
    log_files = _coerce_log_files(data.get("log_files", []))
    cfg = AppConfig(log_files=log_files)
    for field_name in cfg.__dataclass_fields__:
        if field_name == "log_files":
            continue
        if field_name in data:
            setattr(cfg, field_name, data[field_name])
    cfg.gemini_api_key = data.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
    cfg.no_llm = no_llm or os.getenv("LOG_CORR_NO_LLM", "").lower() == "true"
    return cfg
