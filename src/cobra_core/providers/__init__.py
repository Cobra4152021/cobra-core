"""Provider-neutral inference interfaces (placeholders only in Phase 1)."""

from cobra_core.providers.base import (
    GenerationRequest,
    GenerationResult,
    ModelProvider,
    ProviderNotConfiguredError,
)
from cobra_core.providers.registry import get_provider, list_providers

__all__ = [
    "GenerationRequest",
    "GenerationResult",
    "ModelProvider",
    "ProviderNotConfiguredError",
    "get_provider",
    "list_providers",
]
