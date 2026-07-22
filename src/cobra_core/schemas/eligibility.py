"""Runtime and benchmark eligibility rules for ModelManifest."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cobra_core.schemas.manifest import ModelManifest

from cobra_core.schemas.manifest import (
    AcquisitionStatus,
    BenchmarkEligibilityStatus,
    HashVerificationState,
    RuntimeValidationStatus,
)

_BENCHMARK_POSITIVE = frozenset(
    {
        BenchmarkEligibilityStatus.TECHNICALLY_ELIGIBLE,
        BenchmarkEligibilityStatus.INTERIM_ELIGIBLE,
        BenchmarkEligibilityStatus.BENCHMARK_COMPLETED,
    }
)

_RUNTIME_BLOCKS_BENCHMARK = frozenset(
    {
        RuntimeValidationStatus.LOAD_FAILED,
        RuntimeValidationStatus.UNSUPPORTED_ON_ENVIRONMENT,
        RuntimeValidationStatus.QUARANTINED,
    }
)

_BLOCKED_BY_RUNTIME_REQUIRES = frozenset(
    {
        RuntimeValidationStatus.LOAD_FAILED,
        RuntimeValidationStatus.UNSUPPORTED_ON_ENVIRONMENT,
    }
)

_LOADABLE_ACQUISITION = frozenset(
    {
        AcquisitionStatus.ACQUIRED,
        AcquisitionStatus.VERIFIED,
    }
)


def _artifact_hashes_verified(manifest: ModelManifest) -> bool:
    return all(
        item.verification_state in {HashVerificationState.VERIFIED, HashVerificationState.OFFICIAL}
        and item.sha256 is not None
        for item in manifest.artifact_files
    )


def assert_valid_eligibility_combo(manifest: ModelManifest) -> None:
    """Raise ValueError when acquisition, runtime, and benchmark states conflict."""
    acquisition = manifest.acquisition_status
    runtime = manifest.runtime_validation_status
    benchmark = manifest.benchmark_eligibility_status

    if (
        benchmark == BenchmarkEligibilityStatus.BENCHMARK_COMPLETED
        and runtime != RuntimeValidationStatus.LOAD_PASSED
    ):
        raise ValueError(
            "benchmark_eligibility_status=benchmark_completed requires "
            "runtime_validation_status=load_passed"
        )

    if acquisition in _LOADABLE_ACQUISITION and not _artifact_hashes_verified(manifest):
        raise ValueError(
            f"acquisition_status={acquisition.value} requires verified sha256 for every artifact"
        )

    if (
        runtime == RuntimeValidationStatus.LOAD_PASSED
        and acquisition == AcquisitionStatus.QUARANTINED
    ):
        raise ValueError(
            "runtime_validation_status=load_passed is incompatible with "
            "acquisition_status=quarantined"
        )

    if benchmark in _BENCHMARK_POSITIVE and runtime in _RUNTIME_BLOCKS_BENCHMARK:
        raise ValueError(
            f"benchmark_eligibility_status={benchmark.value} is incompatible with "
            f"runtime_validation_status={runtime.value}"
        )

    if (
        benchmark == BenchmarkEligibilityStatus.BLOCKED_BY_RUNTIME
        and runtime not in _BLOCKED_BY_RUNTIME_REQUIRES
    ):
        raise ValueError(
            "benchmark_eligibility_status=blocked_by_runtime requires "
            "runtime_validation_status in {load_failed, unsupported_on_environment}"
        )


def is_benchmark_runnable(manifest: ModelManifest) -> bool:
    """True when benchmark execution is allowed on the current runtime state."""
    if manifest.benchmark_eligibility_status not in {
        BenchmarkEligibilityStatus.TECHNICALLY_ELIGIBLE,
        BenchmarkEligibilityStatus.INTERIM_ELIGIBLE,
    }:
        return False
    if manifest.runtime_validation_status != RuntimeValidationStatus.LOAD_PASSED:
        return False
    if manifest.acquisition_status not in _LOADABLE_ACQUISITION:
        return False
    return _artifact_hashes_verified(manifest)


def environment_blocks_runtime(manifest: ModelManifest) -> bool:
    """True when the recorded environment cannot run this model locally."""
    if manifest.benchmark_eligibility_status == BenchmarkEligibilityStatus.BLOCKED_BY_RUNTIME:
        return True
    return manifest.runtime_validation_status in _BLOCKED_BY_RUNTIME_REQUIRES
