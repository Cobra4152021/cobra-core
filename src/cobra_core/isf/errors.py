"""Typed ISF failures (fail closed; never invent certainty)."""

from __future__ import annotations

from enum import StrEnum


class IsfErrorCode(StrEnum):
    SKILL_NOT_FOUND = "skill_not_found"
    SKILL_VERSION_UNSUPPORTED = "skill_version_unsupported"
    MANIFEST_INVALID = "manifest_invalid"
    MISSING_REQUIRED_EVIDENCE = "missing_required_evidence"
    SCHEMA_VALIDATION_FAILED = "schema_validation_failed"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    CONFIDENCE_BELOW_THRESHOLD = "confidence_below_threshold"
    CAPABILITY_EXPANSION_FAILED = "capability_expansion_failed"
    ROUTING_FAILED = "routing_failed"
    EXECUTION_FAILED = "execution_failed"
    ISF_DISABLED = "isf_disabled"


class IsfError(Exception):
    """Safe, non-leaking ISF failure."""

    def __init__(self, code: IsfErrorCode | str, message: str) -> None:
        if isinstance(code, IsfErrorCode):
            self.code = code
        else:
            self.code = IsfErrorCode(code)
        self.message = message
        super().__init__(message)
