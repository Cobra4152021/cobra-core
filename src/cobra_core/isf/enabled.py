"""ISF feature gate (staging)."""

from __future__ import annotations

import os


def isf_enabled() -> bool:
    """ISF is on by default (KC-025). Set ISF_ENABLED=false to restore legacy Computer→AIR path."""
    raw = os.environ.get("ISF_ENABLED", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}
