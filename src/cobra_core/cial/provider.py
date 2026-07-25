"""Provider-neutral CIAL provider interface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cobra_core.cial.capabilities import Capability
from cobra_core.cial.health import HealthState
from cobra_core.cial.types import GenerateRequest, InferenceResult, ModelRecord


@runtime_checkable
class InferenceProvider(Protocol):
    """
    Adapter boundary for inference backends.

    Implementations must not expose provider SDK objects outside the adapter.
    """

    @property
    def provider_id(self) -> str: ...

    def list_models(self) -> list[ModelRecord]:
        """Models this provider contributes to the registry."""
        ...

    def capabilities(self) -> frozenset[Capability]:
        """Union of capabilities across enabled models (hint for callers)."""
        ...

    def health(self) -> HealthState:
        """Aggregate provider health."""
        ...

    def readiness_check(self) -> bool:
        """Optional readiness probe; True when generate may be attempted."""
        ...

    def generate(self, request: GenerateRequest) -> InferenceResult:
        """Run one completion for request.model_id."""
        ...
