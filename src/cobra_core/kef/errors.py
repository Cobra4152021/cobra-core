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
    EVIDENCE_ACCESS_DENIED = "evidence_access_denied"
    INVALID_EVIDENCE_CITATION = "invalid_evidence_citation"
    EVIDENCE_CONTEXT_BUDGET_EXCEEDED = "evidence_context_budget_exceeded"
    INTEGRITY_MISMATCH = "integrity_mismatch"
    VAULT_TIMEOUT = "vault_timeout"
    VAULT_RATE_LIMITED = "vault_rate_limited"
    VAULT_AUTH_FAILURE = "vault_auth_failure"
    VAULT_FORBIDDEN = "vault_forbidden"


class KefError(Exception):
    """Safe, non-leaking KEF failure."""

    def __init__(self, code: KefErrorCode, message: str | None = None) -> None:
        self.code = code
        self.message = message or code.value.replace("_", " ")
        super().__init__(self.message)
