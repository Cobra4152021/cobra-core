"""Request ID generation and validation (Protocol V1)."""

from __future__ import annotations

import re
import uuid

# Safe caller/server IDs: cc_ prefix preferred; length-bounded; no whitespace/control.
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
MAX_REQUEST_ID_LEN = 128


def is_valid_request_id(value: str) -> bool:
    if not value or len(value) > MAX_REQUEST_ID_LEN:
        return False
    return _REQUEST_ID_RE.fullmatch(value) is not None


def new_request_id(incoming: str | None) -> str:
    """Preserve valid caller ID; otherwise generate cc_<uuid>."""
    raw = (incoming or "").strip()
    if raw and is_valid_request_id(raw):
        return raw
    return f"cc_{uuid.uuid4()}"
