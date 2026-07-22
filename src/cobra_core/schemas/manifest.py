"""ModelManifest — immutable intake record for open-weight evaluation targets."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ArtifactFile(BaseModel):
    """A single model artifact with integrity hash."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    path: Annotated[str, Field(min_length=1, description="Relative or logical artifact path")]
    sha256: Annotated[
        str,
        Field(
            min_length=64,
            max_length=64,
            pattern=r"^[a-fA-F0-9]{64}$",
            description="SHA256 hex digest of the artifact file",
        ),
    ]
    size_bytes: Annotated[int | None, Field(default=None, ge=0)] = None


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
        Field(min_length=1, description="Upstream commit SHA or equivalent pin"),
    ]
    license_name: Annotated[str, Field(min_length=1)]
    license_url: HttpUrl | str | None = None
    artifact_files: Annotated[list[ArtifactFile], Field(min_length=1)]
    parameter_count: Annotated[
        int | None,
        Field(default=None, ge=1, description="Approximate parameter count when known"),
    ] = None
    architecture: Annotated[str, Field(min_length=1)]
    quantization: QuantizationInfo | None = None
    context_window: Annotated[int, Field(ge=1, description="Maximum context length in tokens")]
    acquisition_date: date
    notes: str | None = None

    @field_validator("artifact_files")
    @classmethod
    def unique_artifact_paths(cls, value: list[ArtifactFile]) -> list[ArtifactFile]:
        paths = [item.path for item in value]
        if len(paths) != len(set(paths)):
            raise ValueError("artifact_files paths must be unique")
        return value

    def sha256_map(self) -> dict[str, str]:
        """Return mapping of artifact path -> lowercase SHA256."""
        return {item.path: item.sha256.lower() for item in self.artifact_files}
