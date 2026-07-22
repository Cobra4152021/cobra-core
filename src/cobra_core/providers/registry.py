"""Provider registry for Qwen, Mistral, Gemma, and future families."""

from __future__ import annotations

from cobra_core.providers.base import ModelProvider
from cobra_core.providers.gemma import GemmaProvider
from cobra_core.providers.mistral import MistralProvider
from cobra_core.providers.qwen import QwenProvider

_PROVIDERS: dict[str, ModelProvider] = {
    "qwen": QwenProvider(),
    "mistral": MistralProvider(),
    "gemma": GemmaProvider(),
}


def list_providers() -> list[str]:
    """Return registered provider ids."""
    return sorted(_PROVIDERS)


def get_provider(provider_id: str) -> ModelProvider:
    """Return a provider by id or raise KeyError."""
    try:
        return _PROVIDERS[provider_id]
    except KeyError as exc:
        known = ", ".join(list_providers())
        raise KeyError(f"unknown provider {provider_id!r}; known: {known}") from exc
