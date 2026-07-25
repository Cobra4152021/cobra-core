"""AIR provider/model descriptor registry (registration without router edits)."""

from __future__ import annotations

from cobra_core.air.types import ModelDescriptor, ProviderDescriptor
from cobra_core.cial.errors import CialError, CialErrorCode


class DescriptorRegistry:
    """In-memory registry of provider/model descriptors for AIR."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderDescriptor] = {}
        self._models: dict[tuple[str, str], ModelDescriptor] = {}

    def register_provider(self, provider: ProviderDescriptor) -> None:
        self._providers[provider.provider_id] = provider
        for model in provider.models:
            if model.provider_id != provider.provider_id:
                raise CialError(
                    CialErrorCode.ROUTING_FAILED,
                    "model provider_id must match parent provider",
                )
            self._models[model.key] = model

    def register_model(self, model: ModelDescriptor) -> None:
        if model.provider_id not in self._providers:
            raise CialError(
                CialErrorCode.PROVIDER_NOT_FOUND,
                "register provider before model",
            )
        self._models[model.key] = model
        parent = self._providers[model.provider_id]
        models = tuple(m for m in parent.models if m.key != model.key) + (model,)
        self._providers[model.provider_id] = ProviderDescriptor(
            provider_id=parent.provider_id,
            display_name=parent.display_name,
            models=models,
            enabled=parent.enabled,
            metadata=dict(parent.metadata),
        )

    def get_provider(self, provider_id: str) -> ProviderDescriptor:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise CialError(
                CialErrorCode.PROVIDER_NOT_FOUND,
                "provider not registered",
            ) from exc

    def get_model(self, provider_id: str, model_id: str) -> ModelDescriptor:
        try:
            return self._models[(provider_id, model_id)]
        except KeyError as exc:
            raise CialError(
                CialErrorCode.MODEL_NOT_FOUND,
                "model not registered",
            ) from exc

    def list_models(self) -> list[ModelDescriptor]:
        return list(self._models.values())

    def list_providers(self) -> list[ProviderDescriptor]:
        return list(self._providers.values())

    def __len__(self) -> int:
        return len(self._models)
