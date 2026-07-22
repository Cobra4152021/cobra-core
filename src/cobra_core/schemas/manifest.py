"""ModelManifest — immutable intake record for open-weight evaluation targets."""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

# Known fabricated / example digests that must never pass as verified.
_BLOCKED_SHA256: frozenset[str] = frozenset(
    {
        "0" * 64,
        "f" * 64,
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
    }
)

_UNPINNED_REVISION_PATTERN = re.compile(
    r"^(latest|main|master|head|tip|current|not-acquired|tbd|todo|unknown)$",
    re.IGNORECASE,
)

_PLACEHOLDER_COMMIT_PATTERN = re.compile(
    r"^(0{7,40}|latest|main|master|head|tip|current|not-acquired|tbd|todo|unknown)$",
    re.IGNORECASE,
)


class AcquisitionStatus(StrEnum):
    """Whether weight artifacts have been acquired and validated locally."""

    NOT_ACQUIRED = "not_acquired"
    ACQUIRED = "acquired"
    QUARANTINED = "quarantined"
    FAILED = "failed"


class HashVerificationState(StrEnum):
    """Integrity state for an artifact hash."""

    PENDING = "pending"  # not yet hashed; expected before acquisition
    VERIFIED = "verified"  # locally computed after download
    OFFICIAL = "official"  # published by upstream (rare; must be real)


class ArchitectureFamily(StrEnum):
    """Supported architecture families for Cobra Model Lab intake."""

    TRANSFORMER_DECODER = "transformer-decoder"
    TRANSFORMER_DECODER_MOE = "transformer-decoder-moe"
    UNKNOWN = "unknown"


class ArtifactFile(BaseModel):
    """A single model artifact with optional integrity hash."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    path: Annotated[str, Field(min_length=1, description="Relative or logical artifact path")]
    sha256: Annotated[
        str | None,
        Field(
            default=None,
            description="SHA256 hex digest when known; null while pending",
        ),
    ] = None
    verification_state: HashVerificationState = HashVerificationState.PENDING
    size_bytes: Annotated[int | None, Field(default=None, ge=0)] = None

    @field_validator("sha256")
    @classmethod
    def validate_sha256_format(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digest = value.lower()
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("sha256 must be a 64-character lowercase hex digest or null")
        if digest in _BLOCKED_SHA256:
            raise ValueError(
                "sha256 matches a blocked placeholder/example digest; "
                "do not fabricate hashes before acquisition"
            )
        return digest

    @model_validator(mode="after")
    def hash_state_consistency(self) -> Self:
        if self.verification_state == HashVerificationState.PENDING:
            if self.sha256 is not None:
                raise ValueError(
                    "pending artifacts must not include a sha256 value; "
                    "leave sha256 null until hashed"
                )
        elif self.sha256 is None:
            raise ValueError(
                f"verification_state={self.verification_state.value} requires a real sha256"
            )
        return self


class QuantizationInfo(BaseModel):
    """Optional quantization metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    method: Annotated[str, Field(min_length=1, description="e.g. none, awq, gptq, gguf-q4_k_m")]
    bits: Annotated[int | None, Field(default=None, ge=1, le=32)] = None
    notes: str | None = None


class ModelManifest(BaseModel):
    """
    Provenance and identity record for a candidate model.

    Model weights are NOT stored in this repository. Manifests describe
    what would be acquired and how integrity is verified.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    provider: Annotated[
        str,
        Field(min_length=1, description="Provider family, e.g. qwen, mistral, gemma"),
    ]
    model_name: Annotated[str, Field(min_length=1)]
    model_revision: Annotated[
        str,
        Field(min_length=1, description="Exact revision tag, commit, or release id"),
    ]
    source_repository: Annotated[
        HttpUrl | str,
        Field(description="Upstream source repository URL or identifier"),
    ]
    source_commit: Annotated[
        str,
        Field(min_length=7, description="Upstream commit SHA or equivalent pin"),
    ]
    license_name: Annotated[str, Field(min_length=1)]
    license_url: Annotated[
        HttpUrl | str,
        Field(description="Official license file or license documentation URL"),
    ]
    artifact_files: Annotated[list[ArtifactFile], Field(min_length=1)]
    parameter_count: Annotated[
        int | None,
        Field(default=None, ge=1, description="Approximate parameter count when known"),
    ] = None
    architecture: ArchitectureFamily
    quantization: QuantizationInfo | None = None
    context_window: Annotated[int, Field(ge=1, description="Claimed context length in tokens")]
    context_window_provenance: Annotated[
        str,
        Field(
            min_length=8,
            description="Source note for the context_window claim (model card / docs citation)",
        ),
    ]
    acquisition_status: AcquisitionStatus = AcquisitionStatus.NOT_ACQUIRED
    intake_date: date
    acquisition_date: date | None = None
    notes: str | None = None

    @field_validator("source_repository")
    @classmethod
    def require_source_repository(cls, value: HttpUrl | str) -> HttpUrl | str:
        text = str(value).strip()
        if not text:
            raise ValueError("source_repository is required")
        if text.lower() in {"tbd", "todo", "unknown", "none", "n/a"}:
            raise ValueError("source_repository must be a real upstream URL or identifier")
        return value

    @field_validator("model_revision")
    @classmethod
    def require_pinned_revision(cls, value: str) -> str:
        if _UNPINNED_REVISION_PATTERN.match(value.strip()):
            raise ValueError(
                "model_revision is unpinned; use an exact commit SHA, tag, or dated release id"
            )
        return value

    @field_validator("source_commit")
    @classmethod
    def require_pinned_commit(cls, value: str) -> str:
        cleaned = value.strip()
        if _PLACEHOLDER_COMMIT_PATTERN.match(cleaned):
            raise ValueError("source_commit must be a real pinned commit, not a placeholder")
        if not re.fullmatch(r"[0-9a-fA-F]{7,64}", cleaned):
            raise ValueError("source_commit must look like a git/content commit SHA")
        return cleaned.lower()

    @field_validator("license_name")
    @classmethod
    def require_license_name(cls, value: str) -> str:
        if value.strip().lower() in {
            "",
            "tbd",
            "todo",
            "unknown",
            "none",
            "n/a",
            "unacquired-example",
        }:
            raise ValueError("license_name is missing or placeholder")
        return value

    @field_validator("artifact_files")
    @classmethod
    def unique_artifact_paths(cls, value: list[ArtifactFile]) -> list[ArtifactFile]:
        paths = [item.path for item in value]
        if len(paths) != len(set(paths)):
            raise ValueError("artifact_files paths must be unique")
        return value

    @model_validator(mode="after")
    def acquisition_hash_consistency(self) -> Self:
        states = {item.verification_state for item in self.artifact_files}

        if self.acquisition_status == AcquisitionStatus.NOT_ACQUIRED:
            if self.acquisition_date is not None:
                raise ValueError("not_acquired manifests must not set acquisition_date")
            if any(state != HashVerificationState.PENDING for state in states):
                raise ValueError("not_acquired manifests may only use pending artifact hashes")
        elif self.acquisition_status == AcquisitionStatus.ACQUIRED:
            if self.acquisition_date is None:
                raise ValueError("acquired manifests require acquisition_date")
            if any(
                item.verification_state
                not in {HashVerificationState.VERIFIED, HashVerificationState.OFFICIAL}
                or item.sha256 is None
                for item in self.artifact_files
            ):
                raise ValueError(
                    "acquired manifests require verified/official sha256 for every artifact"
                )
        elif self.acquisition_status in {
            AcquisitionStatus.QUARANTINED,
            AcquisitionStatus.FAILED,
        }:
            if self.acquisition_date is None:
                raise ValueError(
                    f"{self.acquisition_status.value} manifests require acquisition_date"
                )

        if self.architecture == ArchitectureFamily.UNKNOWN:
            raise ValueError("architecture must not be unknown for intake candidates")

        return self

    def sha256_map(self) -> dict[str, str]:
        """Return mapping of artifact path -> lowercase SHA256 for hashed artifacts."""
        return {item.path: item.sha256 for item in self.artifact_files if item.sha256 is not None}
