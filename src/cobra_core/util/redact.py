"""Secret redaction for logs and serialized metadata."""

from __future__ import annotations

import re
from typing import Any

_SECRET_KEYS = re.compile(
    r"(token|password|secret|authorization|api[_-]?key|hf_token|access_key)",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)
_HF_TOKEN = re.compile(r"hf_[A-Za-z0-9]{10,}")


def redact_secrets(value: Any) -> Any:
    """Recursively redact likely secrets from structures and strings."""
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _SECRET_KEYS.search(str(key)):
                out[str(key)] = "[REDACTED]"
            else:
                out[str(key)] = redact_secrets(item)
        return out
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, str):
        text = _BEARER.sub(r"\1[REDACTED]", value)
        text = _HF_TOKEN.sub("hf_[REDACTED]", text)
        return text
    return value
