"""Abstract provider interface — no assumed host, API, GPU, or serving stack."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ProviderNotConfiguredError(RuntimeError):
    """Raised when a provider placeholder is invoked without a configured backend."""


@dataclass(frozen=True)
class GenerationRequest:
    """Provider-neutral generation request."""

    system_prompt: str
    user_prompt: str
    temperature: float = 0.0
    top_p: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    stop: list[str] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResult:
    """Provider-neutral generation result."""

    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class ModelProvider(ABC):
    """
    Interface for evaluating open-weight / hosted models.

    Phase 1 implementations are placeholders only. They must not download
    weights or call remote APIs until explicitly configured in later phases.
    """

    provider_id: str

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True when a concrete backend has been configured."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate a completion. Placeholders must raise if not configured."""
