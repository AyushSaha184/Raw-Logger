from __future__ import annotations

import logging
from typing import Any

try:
    import structlog
except ImportError:  # pragma: no cover
    structlog = None  # type: ignore[assignment]


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(message)s")
    if structlog is not None:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(level),
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
        )


def get_logger(name: str) -> Any:
    if structlog is not None:
        return structlog.get_logger(name)
    return logging.getLogger(name)
