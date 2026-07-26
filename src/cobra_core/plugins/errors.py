"""Plugin framework errors (fail closed)."""

from __future__ import annotations

from enum import StrEnum


class PluginErrorCode(StrEnum):
    MANIFEST_INVALID = "manifest_invalid"
    VALIDATION_FAILED = "validation_failed"
    PERMISSION_DENIED = "permission_denied"
    COMPATIBILITY_FAILED = "compatibility_failed"
    DUPLICATE_ID = "duplicate_id"
    NOT_FOUND = "not_found"
    LOAD_FAILED = "load_failed"
    STATE_INVALID = "state_invalid"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    RESERVED_NAMESPACE = "reserved_namespace"
    DEPENDENCY_MISSING = "dependency_missing"
    TYPE_UNSUPPORTED = "type_unsupported"


class PluginError(Exception):
    def __init__(self, code: PluginErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
