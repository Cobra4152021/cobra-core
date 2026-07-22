"""ModelManifest schema accept/reject tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from cobra_core.schemas.manifest import (
    AcquisitionStatus,
    ArchitectureFamily,
    ArtifactFile,
    BenchmarkEligibilityStatus,
    HashVerificationState,
    ModelManifest,
    RuntimeValidationStatus,
)
from cobra_core.validation import load_json_model, validate_json_dir


def _pending_artifact(path: str = "model.safetensors") -> dict[str, object]:
    return {
        "path": path,
        "sha256": None,
        "verification_state": "pending",
        "size_bytes": None,
    }


def _valid_preacquisition(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "provider": "qwen",
        "model_name": "Qwen3-8B",
        "model_revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "source_repository": "https://huggingface.co/Qwen/Qwen3-8B",
        "source_commit": "b968826d9c46dd6066d109eabc6255188de91218",
        "license_name": "Apache-2.0",
        "license_url": "https://huggingface.co/Qwen/Qwen3-8B/blob/main/LICENSE",
        "artifact_files": [_pending_artifact()],
        "architecture": "transformer-decoder",
        "context_window": 32768,
        "context_window_provenance": "Official Hugging Face model card for Qwen/Qwen3-8B.",
        "acquisition_status": "not_acquired",
        "intake_date": date(2026, 7, 22),
        "acquisition_date": None,
    }
    data.update(overrides)
    return data


def test_valid_preacquisition_manifest_accepted() -> None:
    manifest = ModelManifest.model_validate(_valid_preacquisition())
    assert manifest.acquisition_status == AcquisitionStatus.NOT_ACQUIRED
    assert manifest.architecture == ArchitectureFamily.TRANSFORMER_DECODER
    assert manifest.sha256_map() == {}


def test_qwen_intake_manifests_validate(repo_root: Path) -> None:
    manifests_dir = repo_root / "model-cards"
    manifests, issues = validate_json_dir(manifests_dir, ModelManifest, recursive=True)
    assert issues == []
    by_name = {item.model_name: item for item in manifests}
    assert set(by_name) == {
        "Qwen3-32B",
        "Qwen3-8B",
        "Qwen3-30B-A3B-Thinking-2507",
    }
    assert by_name["Qwen3-30B-A3B-Thinking-2507"].acquisition_status == (
        AcquisitionStatus.NOT_ACQUIRED
    )
    # Development / primary baselines may be verified after Phase 2B/2C.
    for name in ("Qwen3-8B", "Qwen3-32B"):
        model = by_name[name]
        if model.acquisition_status == AcquisitionStatus.NOT_ACQUIRED:
            assert all(
                artifact.verification_state == HashVerificationState.PENDING
                for artifact in model.artifact_files
            )
        else:
            assert model.acquisition_status in {
                AcquisitionStatus.ACQUIRED,
                AcquisitionStatus.VERIFIED,
            }
            assert model.local_artifact_root
            assert all(
                artifact.verification_state == HashVerificationState.VERIFIED and artifact.sha256
                for artifact in model.artifact_files
            )
        eight_b = by_name["Qwen3-8B"]
        assert eight_b.runtime_validation_status == RuntimeValidationStatus.LOAD_PASSED
        assert eight_b.benchmark_eligibility_status in {
            BenchmarkEligibilityStatus.INTERIM_ELIGIBLE,
            BenchmarkEligibilityStatus.BENCHMARK_COMPLETED,
        }
    thirty_two_b = by_name["Qwen3-32B"]
    assert thirty_two_b.runtime_validation_status == (
        RuntimeValidationStatus.UNSUPPORTED_ON_ENVIRONMENT
    )
    assert (
        thirty_two_b.benchmark_eligibility_status == BenchmarkEligibilityStatus.BLOCKED_BY_RUNTIME
    )
    thinking = by_name["Qwen3-30B-A3B-Thinking-2507"]
    assert thinking.runtime_validation_status == RuntimeValidationStatus.NOT_TESTED
    assert thinking.benchmark_eligibility_status == BenchmarkEligibilityStatus.NOT_ELIGIBLE


def test_primary_manifest_file_loads(repo_root: Path) -> None:
    path = repo_root / "model-cards" / "qwen" / "qwen3-32b.manifest.json"
    manifest = load_json_model(path, ModelManifest)
    assert manifest.model_revision == "9216db5781bf21249d130ec9da846c4624c16137"
    assert manifest.source_commit == manifest.model_revision


def test_rejects_placeholder_sha256() -> None:
    with pytest.raises(ValidationError):
        ArtifactFile.model_validate(
            {
                "path": "x",
                "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "verification_state": "verified",
            }
        )


def test_rejects_pending_with_hash() -> None:
    with pytest.raises(ValidationError):
        ArtifactFile.model_validate(
            {
                "path": "x",
                "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "verification_state": "pending",
            }
        )


def test_rejects_acquired_without_verified_hashes() -> None:
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(
            _valid_preacquisition(
                acquisition_status="acquired",
                acquisition_date=date(2026, 7, 22),
            )
        )


def test_rejects_not_acquired_with_acquisition_date() -> None:
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(_valid_preacquisition(acquisition_date=date(2026, 7, 22)))


def test_rejects_unpinned_revision() -> None:
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(_valid_preacquisition(model_revision="latest"))


def test_rejects_placeholder_commit() -> None:
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(_valid_preacquisition(source_commit="0000000"))


def test_rejects_missing_license_url_and_bad_name() -> None:
    payload = _valid_preacquisition()
    del payload["license_url"]
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(payload)
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(_valid_preacquisition(license_name="UNACQUIRED-EXAMPLE"))


def test_rejects_missing_context_provenance() -> None:
    payload = _valid_preacquisition()
    del payload["context_window_provenance"]
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(payload)


def test_rejects_unknown_architecture() -> None:
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(_valid_preacquisition(architecture="unknown"))


def test_rejects_unsupported_architecture_string() -> None:
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(_valid_preacquisition(architecture="diffusion-unet"))


def test_rejects_duplicate_artifact_paths() -> None:
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(
            _valid_preacquisition(
                artifact_files=[
                    _pending_artifact("same.safetensors"),
                    _pending_artifact("same.safetensors"),
                ]
            )
        )


def test_verified_manifest_requires_real_hashes() -> None:
    digest = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    manifest = ModelManifest.model_validate(
        _valid_preacquisition(
            acquisition_status="verified",
            acquisition_date=date(2026, 7, 22),
            local_artifact_root="D:/cobra-models/qwen/qwen3-8b/rev/artifacts",
            local_inventory_ref="D:/cobra-models/qwen/qwen3-8b/rev/provenance/artifact-inventory.json",
            artifact_files=[
                {
                    "path": "model.safetensors",
                    "sha256": digest,
                    "verification_state": "verified",
                    "size_bytes": 1,
                }
            ],
        )
    )
    assert manifest.sha256_map()["model.safetensors"] == digest


def test_acquired_manifest_requires_real_hashes() -> None:
    digest = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    manifest = ModelManifest.model_validate(
        _valid_preacquisition(
            acquisition_status="acquired",
            acquisition_date=date(2026, 7, 22),
            local_artifact_root="D:/cobra-models/qwen/qwen3-8b/rev/artifacts",
            local_inventory_ref="D:/cobra-models/qwen/qwen3-8b/rev/provenance/artifact-inventory.json",
            artifact_files=[
                {
                    "path": "model.safetensors",
                    "sha256": digest,
                    "verification_state": "verified",
                    "size_bytes": 1,
                }
            ],
        )
    )
    assert manifest.sha256_map()["model.safetensors"] == digest
