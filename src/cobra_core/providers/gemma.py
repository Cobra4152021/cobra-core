"""Gemma provider placeholder — interface only in Phase 1."""

from __future__ import annotations

from cobra_core.providers.base import (
    GenerationRequest,
    GenerationResult,
    ModelProvider,
    ProviderNotConfiguredError,
)


class GemmaProvider(ModelProvider):
    """Placeholder for Gemma-family models. Does not download weights."""

    provider_id = "gemma"

    def is_configured(self) -> bool:
        return False

    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise ProviderNotConfiguredError(
            "GemmaProvider is a Phase 1 placeholder. Configure a backend before inference. "
            "No model weights are downloaded by this repository."
        )
