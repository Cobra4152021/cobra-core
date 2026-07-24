"""Bearer authentication — never log or echo secrets."""

from __future__ import annotations

import hmac
import secrets


def extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def verify_bearer(authorization: str | None, expected_secret: str) -> bool:
    """Constant-time compare when lengths match; reject missing/mismatched safely."""
    if not expected_secret:
        return False
    provided = extract_bearer(authorization)
    if provided is None:
        return False
    # hmac.compare_digest requires equal length; pad via secrets.compare for mismatch lengths.
    a = provided.encode("utf-8")
    b = expected_secret.encode("utf-8")
    if len(a) != len(b):
        # Still perform a dummy compare to reduce trivial timing signal on length.
        dummy = secrets.token_bytes(len(b))
        hmac.compare_digest(dummy, b)
        return False
    return hmac.compare_digest(a, b)
