"""Cryptographically bind public API identity headers to the authenticated request."""

from __future__ import annotations

import hashlib
import hmac
import time
from collections.abc import Mapping
from dataclasses import dataclass

IDENTITY_ASSERTION_MAX_AGE_SECONDS = 300


@dataclass(frozen=True)
class VerifiedIdentity:
    principal_id: str
    organization_id: str
    timestamp: int


def _header(headers: Mapping[str, str], name: str) -> str:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return str(value or "").strip()
    return ""


def identity_assertion_payload(
    *,
    timestamp: int,
    principal_id: str,
    organization_id: str,
    method: str,
    path: str,
) -> bytes:
    return (f"{timestamp}\n{principal_id}\n{organization_id}\n{method.upper()}\n{path}").encode()


def sign_identity_assertion(
    *,
    secret: str,
    timestamp: int,
    principal_id: str,
    organization_id: str,
    method: str,
    path: str,
) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        identity_assertion_payload(
            timestamp=timestamp,
            principal_id=principal_id,
            organization_id=organization_id,
            method=method,
            path=path,
        ),
        hashlib.sha256,
    ).hexdigest()


def verify_identity_assertion(
    *,
    headers: Mapping[str, str],
    secret: str,
    method: str,
    path: str,
    now: int | None = None,
    max_age_seconds: int = IDENTITY_ASSERTION_MAX_AGE_SECONDS,
) -> VerifiedIdentity | None:
    """Return a verified identity or None. Missing, stale, or malformed claims fail closed."""
    principal_id = _header(headers, "X-Cobra-Principal-Id")
    organization_id = _header(headers, "X-Cobra-Org-Id")
    timestamp_raw = _header(headers, "X-Cobra-Identity-Timestamp")
    signature = _header(headers, "X-Cobra-Identity-Signature").lower()
    if not secret or not principal_id or not organization_id or not timestamp_raw or not signature:
        return None
    try:
        timestamp = int(timestamp_raw)
    except ValueError:
        return None
    current = int(time.time() if now is None else now)
    if timestamp > current + 30 or current - timestamp > max_age_seconds:
        return None
    expected = sign_identity_assertion(
        secret=secret,
        timestamp=timestamp,
        principal_id=principal_id,
        organization_id=organization_id,
        method=method,
        path=path,
    )
    if not hmac.compare_digest(signature, expected):
        return None
    return VerifiedIdentity(
        principal_id=principal_id,
        organization_id=organization_id,
        timestamp=timestamp,
    )
