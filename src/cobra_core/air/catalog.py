"""
Built-in AIR descriptors for mock + openai-compatible (KC-021).

Future providers: register additional ProviderDescriptor entries only —
no AdaptiveRouter code changes required.
"""

from __future__ import annotations

from cobra_core.air.capabilities import AirCapability
from cobra_core.air.registry import DescriptorRegistry
from cobra_core.air.types import (
    CostClass,
    LatencyClass,
    ModelDescriptor,
    ProviderDescriptor,
)
from cobra_core.cial.health import HealthState
from cobra_core.protocol_v1.constants import DEFAULT_MODEL


def _caps(*values: AirCapability) -> frozenset[AirCapability]:
    return frozenset(values)


def build_default_catalog(
    *,
    mock_model_id: str = DEFAULT_MODEL,
    openai_model_id: str = "gpt-5.4-mini",
    openai_enabled: bool = False,
    openai_health: HealthState = HealthState.UNKNOWN,
) -> DescriptorRegistry:
    """
    Seed mock (always) and optional openai-compatible model.

    OpenAI is registered only when the live gate is ready so AIR cannot
    select a live vendor while disabled.
    """
    reg = DescriptorRegistry()

    mock_model = ModelDescriptor(
        provider_id="mock",
        model_id=mock_model_id,
        capabilities=_caps(
            AirCapability.TEXT,
            AirCapability.OFFLINE,
            AirCapability.REASONING,
            AirCapability.SUMMARIZATION,
            AirCapability.CLASSIFICATION,
            AirCapability.STRUCTURED_OUTPUT,
            AirCapability.CODING,
            AirCapability.RESEARCH,
            AirCapability.TRANSLATION,
            AirCapability.LONG_CONTEXT,
        ),
        estimated_cost=CostClass.LOW,
        latency=LatencyClass.FAST,
        health=HealthState.HEALTHY,
        enabled=True,
        requires_live=False,
        metadata={"wire_identity": True},
    )
    reg.register_provider(
        ProviderDescriptor(
            provider_id="mock",
            display_name="Cobra Core Mock",
            models=(mock_model,),
            enabled=True,
        )
    )

    if openai_enabled:
        openai_model = ModelDescriptor(
            provider_id="openai",
            model_id=openai_model_id,
            capabilities=_caps(
                AirCapability.TEXT,
                AirCapability.REASONING,
                AirCapability.VISION,
                AirCapability.OCR,
                AirCapability.SUMMARIZATION,
                AirCapability.CLASSIFICATION,
                AirCapability.STRUCTURED_OUTPUT,
                AirCapability.CODING,
                AirCapability.RESEARCH,
                AirCapability.TRANSLATION,
                AirCapability.LONG_CONTEXT,
            ),
            estimated_cost=CostClass.LOW,
            latency=LatencyClass.NORMAL,
            health=openai_health,
            enabled=True,
            requires_live=True,
            metadata={"api": "openai-compatible"},
        )
        reg.register_provider(
            ProviderDescriptor(
                provider_id="openai",
                display_name="OpenAI-compatible",
                models=(openai_model,),
                enabled=True,
            )
        )

    return reg
