"""Mistral provider placeholder — interface only in Phase 1."""

from __future__ import annotations

from cobra_core.providers.base import (
    GenerationRequest,
    GenerationResult,
    ModelProvider,
    ProviderNotConfiguredError,
)


class MistralProvider(ModelProvider):
    """Placeholder for Mistral-family models. Does not download weights."""

    provider_id = "mistral"

    def is_configured(self) -> bool:
        return False

    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise ProviderNotConfiguredError(
            "MistralProvider is a Phase 1 placeholder. Configure a backend before inference. "
            "No model weights are downloaded by this repository."
        )
