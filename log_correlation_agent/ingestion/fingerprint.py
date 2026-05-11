from __future__ import annotations

import hashlib
import re

UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
NUMBER_RE = re.compile(r"\b\d+\b")
HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")


def normalize_message(message: str) -> str:
    value = message.lower()
    value = UUID_RE.sub("<uuid>", value)
    value = IP_RE.sub("<ip>", value)
    value = EMAIL_RE.sub("<email>", value)
    value = HEX_RE.sub("<hex>", value)
    value = NUMBER_RE.sub("<num>", value)
    return " ".join(value.split())


def event_signature(message: str) -> str:
    return hashlib.sha256(normalize_message(message).encode("utf-8")).hexdigest()[:24]
