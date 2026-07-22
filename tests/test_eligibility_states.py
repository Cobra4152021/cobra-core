"""Phase 2D Gate 2 — runtime and benchmark eligibility state tests."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from cobra_core.schemas.eligibility import (
    assert_valid_eligibility_combo,
    environment_blocks_runtime,
    is_benchmark_runnable,
)
from cobra_core.schemas.manifest import (
    AcquisitionStatus,
    BenchmarkEligibilityStatus,
    ModelManifest,
    RuntimeValidationStatus,
)

_DIGEST = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def _verified_artifact(path: str = "model.safetensors") -> dict[str, object]:
    return {
        "path": path,
        "sha256": _DIGEST,
        "verification_state": "verified",
        "size_bytes": 1,
    }


def _base_manifest(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "provider": "qwen",
        "model_name": "Qwen3-8B",
        "model_revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "source_repository": "https://huggingface.co/Qwen/Qwen3-8B",
        "source_commit": "b968826d9c46dd6066d109eabc6255188de91218",
        "license_name": "Apache-2.0",
        "license_url": "https://huggingface.co/Qwen/Qwen3-8B/blob/main/LICENSE",
        "artifact_files": [_verified_artifact()],
        "architecture": "transformer-decoder",
        "context_window": 32768,
        "context_window_provenance": "Official Hugging Face model card for Qwen/Qwen3-8B.",
        "acquisition_status": "verified",
        "intake_date": date(2026, 7, 22),
        "acquisition_date": date(2026, 7, 22),
        "local_artifact_root": "D:/cobra-models/qwen/qwen3-8b/rev/artifacts",
        "local_inventory_ref": "D:/cobra-models/qwen/qwen3-8b/rev/provenance/artifact-inventory.json",
    }
    data.update(overrides)
    return data


def test_valid_8b_like_combo() -> None:
    manifest = ModelManifest.model_validate(
        _base_manifest(
            runtime_validation_status="load_passed",
            benchmark_eligibility_status="interim_eligible",
            runtime_environment_key="local-windows-rtx4070-12gb",
            runtime_validation_notes="Phase 2B smoke load passed.",
            runtime_validated_at=date(2026, 7, 22),
        )
    )
    assert manifest.acquisition_status == AcquisitionStatus.VERIFIED
    assert manifest.runtime_validation_status == RuntimeValidationStatus.LOAD_PASSED
    assert manifest.benchmark_eligibility_status == BenchmarkEligibilityStatus.INTERIM_ELIGIBLE
    assert is_benchmark_runnable(manifest) is True
    assert environment_blocks_runtime(manifest) is False


def test_valid_32b_blocked_combo() -> None:
    manifest = ModelManifest.model_validate(
        _base_manifest(
            model_name="Qwen3-32B",
            model_revision="9216db5781bf21249d130ec9da846c4624c16137",
            source_commit="9216db5781bf21249d130ec9da846c4624c16137",
            acquisition_status="verified",
            runtime_validation_status="unsupported_on_environment",
            benchmark_eligibility_status="blocked_by_runtime",
            runtime_environment_key="local-windows-rtx4070-12gb",
            runtime_validation_notes="Local inference load crashed.",
            runtime_validated_at=date(2026, 7, 22),
        )
    )
    assert manifest.benchmark_eligibility_status == BenchmarkEligibilityStatus.BLOCKED_BY_RUNTIME
    assert is_benchmark_runnable(manifest) is False
    assert environment_blocks_runtime(manifest) is True


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        (
            {
                "runtime_validation_status": "not_tested",
                "benchmark_eligibility_status": "benchmark_completed",
            },
            "benchmark_completed requires",
        ),
        (
            {
                "acquisition_status": "verified",
                "artifact_files": [
                    {
                        "path": "model.safetensors",
                        "sha256": None,
                        "verification_state": "pending",
                    }
                ],
            },
            "verified/official sha256",
        ),
        (
            {
                "acquisition_status": "quarantined",
                "acquisition_date": date(2026, 7, 22),
                "runtime_validation_status": "load_passed",
                "benchmark_eligibility_status": "not_eligible",
            },
            "load_passed is incompatible with acquisition_status=quarantined",
        ),
        (
            {
                "runtime_validation_status": "load_failed",
                "benchmark_eligibility_status": "interim_eligible",
            },
            "interim_eligible is incompatible with runtime_validation_status=load_failed",
        ),
        (
            {
                "runtime_validation_status": "unsupported_on_environment",
                "benchmark_eligibility_status": "technically_eligible",
            },
            "technically_eligible is incompatible",
        ),
        (
            {
                "runtime_validation_status": "quarantined",
                "benchmark_eligibility_status": "benchmark_completed",
            },
            "benchmark_completed requires runtime_validation_status=load_passed",
        ),
        (
            {
                "runtime_validation_status": "not_tested",
                "benchmark_eligibility_status": "blocked_by_runtime",
            },
            "blocked_by_runtime requires",
        ),
        (
            {
                "acquisition_status": "acquired",
                "artifact_files": [
                    {
                        "path": "model.safetensors",
                        "sha256": None,
                        "verification_state": "pending",
                    }
                ],
            },
            "verified/official sha256",
        ),
    ],
)
def test_invalid_eligibility_combinations(overrides: dict[str, object], match: str) -> None:
    with pytest.raises(ValidationError, match=match):
        ModelManifest.model_validate(_base_manifest(**overrides))


def test_assert_valid_eligibility_combo_raises_directly() -> None:
    manifest = ModelManifest.model_construct(
        acquisition_status=AcquisitionStatus.VERIFIED,
        runtime_validation_status=RuntimeValidationStatus.LOAD_FAILED,
        benchmark_eligibility_status=BenchmarkEligibilityStatus.INTERIM_ELIGIBLE,
        artifact_files=[],
    )
    with pytest.raises(ValueError, match="interim_eligible is incompatible"):
        assert_valid_eligibility_combo(manifest)


def test_is_benchmark_runnable_false_when_not_eligible() -> None:
    manifest = ModelManifest.model_validate(
        _base_manifest(
            runtime_validation_status="load_passed",
            benchmark_eligibility_status="not_eligible",
        )
    )
    assert is_benchmark_runnable(manifest) is False


def test_is_benchmark_runnable_false_when_runtime_not_passed() -> None:
    manifest = ModelManifest.model_validate(
        _base_manifest(
            runtime_validation_status="not_tested",
            benchmark_eligibility_status="interim_eligible",
        )
    )
    assert is_benchmark_runnable(manifest) is False


def test_verified_manifest_missing_hashes_rejected() -> None:
    with pytest.raises(ValidationError, match="verified manifests require"):
        ModelManifest.model_validate(
            _base_manifest(
                acquisition_status="verified",
                artifact_files=[
                    {
                        "path": "model.safetensors",
                        "sha256": None,
                        "verification_state": "pending",
                    }
                ],
            )
        )
