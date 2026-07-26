"""Opaque session token helpers — no OAuth/OIDC; no credential persistence."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def issue_opaque_token() -> str:
    """Return a high-entropy opaque token (not a JWT)."""
    return secrets.token_urlsafe(32)


def token_fingerprint(token: str) -> str:
    """Stable non-reversible fingerprint for logs/UI (never store raw tokens in audit)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def constant_time_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
