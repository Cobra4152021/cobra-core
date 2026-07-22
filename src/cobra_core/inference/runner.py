"""Inference runner stub — Phase 1 does not execute model calls."""

from __future__ import annotations

from cobra_core.providers.base import GenerationRequest, GenerationResult, ModelProvider


class InferenceNotAvailableError(RuntimeError):
    """Raised when inference is requested before a provider backend is configured."""


class InferenceRunner:
    """
    Thin orchestration wrapper around a ModelProvider.

    Phase 1: validates wiring only; does not download weights or fine-tune.
    """

    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def run(self, request: GenerationRequest) -> GenerationResult:
        if not self.provider.is_configured():
            raise InferenceNotAvailableError(
                f"Provider {self.provider.provider_id!r} is not configured. "
                "Baseline evaluation backends are added in later phases."
            )
        return self.provider.generate(request)
