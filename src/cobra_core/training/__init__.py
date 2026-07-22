"""Training package — intentionally non-operational in Phase 1."""

from cobra_core.training.guard import TrainingNotEnabledError, assert_training_disabled

__all__ = ["TrainingNotEnabledError", "assert_training_disabled"]
