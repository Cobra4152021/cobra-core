"""Model and provider registries for CIAL."""

from __future__ import annotations

from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.health import HealthState
from cobra_core.cial.provider import InferenceProvider
from cobra_core.cial.types import ModelRecord


class ModelRegistry:
    """In-memory registry of ModelRecord entries keyed by (provider_id, model_id)."""

    def __init__(self) -> None:
        self._models: dict[tuple[str, str], ModelRecord] = {}

    def register(self, model: ModelRecord) -> None:
        key = model.key
        if key in self._models:
            raise CialError(
                CialErrorCode.ROUTING_FAILED,
                f"duplicate model registration: {model.provider_id}/{model.model_id}",
            )
        self._models[key] = model

    def register_or_replace(self, model: ModelRecord) -> None:
        self._models[model.key] = model

    def get(self, provider_id: str, model_id: str) -> ModelRecord:
        key = (provider_id, model_id)
        if key not in self._models:
            raise CialError(
                CialErrorCode.MODEL_NOT_FOUND,
                f"model not found: {provider_id}/{model_id}",
            )
        return self._models[key]

    def get_by_model_id(self, model_id: str) -> ModelRecord:
        matches = [m for m in self._models.values() if m.model_id == model_id]
        if not matches:
            raise CialError(CialErrorCode.MODEL_NOT_FOUND, f"model not found: {model_id}")
        if len(matches) > 1:
            # Deterministic: prefer lexicographically smallest provider_id.
            matches.sort(key=lambda m: m.provider_id)
        return matches[0]

    def list_models(self) -> list[ModelRecord]:
        return sorted(self._models.values(), key=lambda m: (m.provider_id, m.model_id))

    def update_health(self, provider_id: str, model_id: str, health: HealthState) -> ModelRecord:
        current = self.get(provider_id, model_id)
        updated = ModelRecord(
            provider_id=current.provider_id,
            model_id=current.model_id,
            display_name=current.display_name,
            enabled=current.enabled,
            capabilities=current.capabilities,
            context_window=current.context_window,
            max_output_tokens=current.max_output_tokens,
            supports_json=current.supports_json,
            supports_tools=current.supports_tools,
            supports_vision=current.supports_vision,
            supports_streaming=current.supports_streaming,
            quality_tier=current.quality_tier,
            latency_tier=current.latency_tier,
            estimated_input_cost=current.estimated_input_cost,
            estimated_output_cost=current.estimated_output_cost,
            revision=current.revision,
            metadata=dict(current.metadata),
            health=health,
        )
        self._models[updated.key] = updated
        return updated

    def __len__(self) -> int:
        return len(self._models)


class ProviderRegistry:
    """In-memory registry of InferenceProvider adapters."""

    def __init__(self) -> None:
        self._providers: dict[str, InferenceProvider] = {}

    def register(self, provider: InferenceProvider) -> None:
        pid = provider.provider_id
        if pid in self._providers:
            raise CialError(
                CialErrorCode.ROUTING_FAILED,
                f"duplicate provider registration: {pid}",
            )
        self._providers[pid] = provider

    def get(self, provider_id: str) -> InferenceProvider:
        if provider_id not in self._providers:
            raise CialError(
                CialErrorCode.PROVIDER_NOT_FOUND,
                f"provider not found: {provider_id}",
            )
        return self._providers[provider_id]

    def list_providers(self) -> list[InferenceProvider]:
        return [self._providers[k] for k in sorted(self._providers)]

    def __len__(self) -> int:
        return len(self._providers)

    def register_provider_models(self, provider: InferenceProvider, models: ModelRegistry) -> None:
        """Register provider then contribute its models into the model registry."""
        self.register(provider)
        for model in provider.list_models():
            models.register(model)
