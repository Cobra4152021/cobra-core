"""
Mock CIAL provider — wraps Protocol V1 mock_complete.

Preserves Internal Alpha deterministic behavior and wire model identity
``cobra-core-qwen3-8b``. No network calls.
"""

from __future__ import annotations

from cobra_core.cial.capabilities import Capability
from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.health import HealthState
from cobra_core.cial.types import (
    GenerateRequest,
    InferenceResult,
    LatencyTier,
    ModelRecord,
    QualityTier,
)
from cobra_core.protocol_v1.constants import DEFAULT_MODEL
from cobra_core.protocol_v1.inference import (
    InferenceCancelledError,
    InferenceFailedError,
    mock_complete,
)

PROVIDER_ID = "mock"


class MockProvider:
    """CIAL adapter over the existing deterministic mock_complete backend."""

    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL,
        revision: str = "mock-v1",
        health: HealthState = HealthState.HEALTHY,
        enabled: bool = True,
        extra_models: list[ModelRecord] | None = None,
    ) -> None:
        self._provider_id = PROVIDER_ID
        self._health = health
        primary = ModelRecord(
            provider_id=PROVIDER_ID,
            model_id=model_id,
            display_name="Cobra Core Mock (Qwen3-8B identity)",
            enabled=enabled,
            capabilities=frozenset(
                {
                    Capability.TEXT,
                    Capability.JSON,
                    Capability.REASONING,
                    Capability.RESEARCH,
                }
            ),
            context_window=8192,
            max_output_tokens=2048,
            supports_json=True,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=False,
            quality_tier=QualityTier.STANDARD,
            latency_tier=LatencyTier.FAST,
            estimated_input_cost=0.0,
            estimated_output_cost=0.0,
            revision=revision,
            metadata={"wire_identity": True, "backend": "mock_complete"},
            health=health,
        )
        self._models: dict[str, ModelRecord] = {primary.model_id: primary}
        for model in extra_models or []:
            if model.provider_id != PROVIDER_ID:
                raise CialError(
                    CialErrorCode.ROUTING_FAILED,
                    "extra mock models must use provider_id=mock",
                )
            self._models[model.model_id] = model

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def list_models(self) -> list[ModelRecord]:
        return sorted(self._models.values(), key=lambda m: m.model_id)

    def capabilities(self) -> frozenset[Capability]:
        caps: set[Capability] = set()
        for model in self._models.values():
            if model.enabled:
                caps |= set(model.capabilities)
        return frozenset(caps)

    def health(self) -> HealthState:
        return self._health

    def set_health(self, health: HealthState) -> None:
        self._health = health
        for mid, model in list(self._models.items()):
            self._models[mid] = ModelRecord(
                provider_id=model.provider_id,
                model_id=model.model_id,
                display_name=model.display_name,
                enabled=model.enabled,
                capabilities=model.capabilities,
                context_window=model.context_window,
                max_output_tokens=model.max_output_tokens,
                supports_json=model.supports_json,
                supports_tools=model.supports_tools,
                supports_vision=model.supports_vision,
                supports_streaming=model.supports_streaming,
                quality_tier=model.quality_tier,
                latency_tier=model.latency_tier,
                estimated_input_cost=model.estimated_input_cost,
                estimated_output_cost=model.estimated_output_cost,
                revision=model.revision,
                metadata=dict(model.metadata),
                health=health,
            )

    def readiness_check(self) -> bool:
        return self._health not in {HealthState.UNAVAILABLE, HealthState.DISABLED}

    def generate(self, request: GenerateRequest) -> InferenceResult:
        if request.model_id not in self._models:
            raise CialError(
                CialErrorCode.MODEL_NOT_FOUND,
                f"mock model not found: {request.model_id}",
            )
        model = self._models[request.model_id]
        if not model.enabled or model.health == HealthState.DISABLED:
            raise CialError(CialErrorCode.MODEL_DISABLED, "mock model is disabled")
        if model.health == HealthState.UNAVAILABLE or not self.readiness_check():
            raise CialError(
                CialErrorCode.PROVIDER_UNAVAILABLE,
                "mock provider is unavailable",
            )

        try:
            result = mock_complete(
                request.messages,
                request.max_tokens,
                delay_ms=request.delay_ms,
                cancel_event=request.cancel_event,
                fail=request.fail,
            )
        except InferenceCancelledError:
            raise
        except InferenceFailedError as exc:
            raise CialError(CialErrorCode.INFERENCE_FAILED, exc.message) from None
        except Exception as exc:
            raise CialError(
                CialErrorCode.INFERENCE_FAILED,
                "mock inference failed",
            ) from exc

        return InferenceResult(
            content=result.content,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            inference_ms=result.inference_ms,
            cial_provider_id=PROVIDER_ID,
            cial_model_id=request.model_id,
            cial_latency_ms=result.inference_ms,
            cial_health_state=model.health.value,
        )
