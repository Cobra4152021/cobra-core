"""Qwen provider placeholder — first evaluation target, not yet configured."""

from __future__ import annotations

from cobra_core.providers.base import (
    GenerationRequest,
    GenerationResult,
    ModelProvider,
    ProviderNotConfiguredError,
)


class QwenProvider(ModelProvider):
    """Placeholder for Qwen-family models. Does not download weights."""

    provider_id = "qwen"

    def is_configured(self) -> bool:
        return False

    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise ProviderNotConfiguredError(
            "QwenProvider is a Phase 1 placeholder. Configure a backend before inference. "
            "No model weights are downloaded by this repository."
        )
