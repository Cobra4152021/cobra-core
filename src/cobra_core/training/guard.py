"""Guards that keep fine-tuning disabled until baseline evaluation exists."""

from __future__ import annotations


class TrainingNotEnabledError(RuntimeError):
    """Raised when training/fine-tuning is attempted before Phase 5 approval."""


def assert_training_disabled() -> None:
    """
    Phase 1 hard stop.

    No fine-tuning occurs before baseline evaluation (Phases 1–4).
    LoRA / adapter training is planned for Phase 5 only.
    """
    raise TrainingNotEnabledError(
        "Training is disabled in Phase 1. Complete model intake and baseline "
        "benchmarking before any LoRA or fine-tuning work (Phase 5)."
    )
