"""ISPF errors (fail closed)."""

from __future__ import annotations

from enum import StrEnum


class SecurityErrorCode(StrEnum):
    UNAUTHENTICATED = "unauthenticated"
    PRINCIPAL_NOT_FOUND = "principal_not_found"
    ROLE_NOT_FOUND = "role_not_found"
    PERMISSION_UNKNOWN = "permission_unknown"
    POLICY_INVALID = "policy_invalid"
    SESSION_NOT_FOUND = "session_not_found"
    SESSION_REVOKED = "session_revoked"
    SESSION_EXPIRED = "session_expired"
    AUTHORIZATION_DENIED = "authorization_denied"
    CONFIG_INVALID = "config_invalid"


class SecurityError(Exception):
    def __init__(self, code: SecurityErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
