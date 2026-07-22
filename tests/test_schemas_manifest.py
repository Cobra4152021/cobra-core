"""ModelManifest schema accept/reject tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from cobra_core.schemas.manifest import ArtifactFile, ModelManifest
from cobra_core.validation import load_json_model


def _valid_manifest(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "provider": "qwen",
        "model_name": "example",
        "model_revision": "rev1",
        "source_repository": "https://example.invalid/model",
        "source_commit": "abc123",
        "license_name": "Example",
        "artifact_files": [
            {
                "path": "model.safetensors",
                "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            }
        ],
        "architecture": "transformer-decoder",
        "context_window": 8192,
        "acquisition_date": date(2026, 7, 22),
    }
    data.update(overrides)
    return data


def test_valid_manifest_accepted() -> None:
    manifest = ModelManifest.model_validate(_valid_manifest())
    assert manifest.provider == "qwen"
    assert len(manifest.sha256_map()) == 1


def test_example_manifest_file_validates(example_manifest_path: Path) -> None:
    manifest = load_json_model(example_manifest_path, ModelManifest)
    assert manifest.model_revision == "not-acquired"


def test_rejects_bad_sha256() -> None:
    with pytest.raises(ValidationError):
        ArtifactFile.model_validate({"path": "x", "sha256": "not-a-hash"})


def test_rejects_missing_artifacts() -> None:
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(_valid_manifest(artifact_files=[]))


def test_rejects_duplicate_artifact_paths() -> None:
    payload = _valid_manifest(
        artifact_files=[
            {
                "path": "same.safetensors",
                "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            },
            {
                "path": "same.safetensors",
                "sha256": "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
            },
        ]
    )
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(payload)


def test_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(_valid_manifest(secret_key="nope"))
