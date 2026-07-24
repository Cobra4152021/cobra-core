"""Structured, redacted logging for Protocol V1 (no secrets/prompts/bodies)."""

from __future__ import annotations

import logging
from typing import Any

from cobra_core.util.redact import redact_secrets

logger = logging.getLogger("cobra_core.protocol_v1")

# Fields never permitted in structured log records (defense in depth).
_FORBIDDEN_KEYS = frozenset(
    {
        "authorization",
        "auth",
        "token",
        "secret",
        "password",
        "prompt",
        "messages",
        "content",
        "body",
        "raw",
        "traceback",
        "stack",
        "exception",
        "env",
        "environ",
        "path",
        "cache",
    }
)


def sanitize_log_fields(fields: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in fields.items():
        lk = str(key).lower()
        if lk in _FORBIDDEN_KEYS or any(p in lk for p in ("secret", "token", "password", "auth")):
            continue
        out[str(key)] = redact_secrets(value)
    return out


def log_event(event: str, **fields: Any) -> None:
    safe = sanitize_log_fields(fields)
    # Single-line structured-ish log; values already redacted.
    parts = [f"event={event}"]
    for key in sorted(safe):
        parts.append(f"{key}={safe[key]!r}")
    logger.info(" ".join(parts))
