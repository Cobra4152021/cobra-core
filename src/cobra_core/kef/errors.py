"""Typed KEF failures (fail closed; safe public messages)."""

from __future__ import annotations

from enum import StrEnum


class KefErrorCode(StrEnum):
    MISSING_REQUIRED_EVIDENCE = "missing_required_evidence"
    PERMISSION_DENIED = "permission_denied"
    UNSUPPORTED_EVIDENCE_TYPE = "unsupported_evidence_type"
    INTEGRITY_FAILURE = "integrity_failure"
    CONNECTOR_UNAVAILABLE = "connector_unavailable"
    CONNECTOR_NOT_FOUND = "connector_not_found"
    RETRIEVAL_FAILED = "retrieval_failed"
    INVALID_REQUEST = "invalid_request"
    KEF_DISABLED = "kef_disabled"
    NOT_IMPLEMENTED = "not_implemented"


class KefError(Exception):
    """Safe, non-leaking KEF failure."""

    def __init__(self, code: KefErrorCode, message: str | None = None) -> None:
        self.code = code
        self.message = message or code.value.replace("_", " ")
        super().__init__(self.message)
