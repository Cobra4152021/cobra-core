"""CIAL engine: route + generate through registered providers."""

from __future__ import annotations

import threading
import time
from typing import Any

from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.errors import CialError, to_inference_failed
from cobra_core.cial.providers.mock import MockProvider
from cobra_core.cial.providers.openai_compatible import OpenAICompatibleProvider
from cobra_core.cial.registry import ModelRegistry, ProviderRegistry
from cobra_core.cial.router import DeterministicRouter
from cobra_core.cial.types import (
    GenerateRequest,
    InferenceResult,
    RoutingPolicy,
    RoutingRequest,
)
from cobra_core.protocol_v1.constants import DEFAULT_MODEL
from cobra_core.protocol_v1.inference import (
    InferenceCancelledError,
)
from cobra_core.protocol_v1.inference import (
    InferenceResult as ProtoResult,
)


class CialEngine:
    """
    Orchestrates deterministic routing and provider generation.

    Phase 2 registers mock (always) and openai-compatible (when configured).
    Automatic fallback remains out of scope.
    """

    def __init__(
        self,
        *,
        config: CialConfig | None = None,
        providers: ProviderRegistry | None = None,
        models: ModelRegistry | None = None,
        router: DeterministicRouter | None = None,
    ) -> None:
        self.config = config or load_cial_config()
        self.providers = providers or ProviderRegistry()
        self.models = models or ModelRegistry()
        self.router = router or DeterministicRouter(self.models)

    @classmethod
    def build_default(cls, config: CialConfig | None = None) -> CialEngine:
        """
        Construct an engine with mock always registered.

        OpenAI-compatible provider is registered only when ``OPENAI_API_KEY``
        is present (or when tests inject a configured provider via constructor).
        """
        cfg = config or load_cial_config()
        engine = cls(config=cfg)
        # Wire Protocol identity stays on mock for KC-018 compatibility.
        mock_model_id = cfg.default_model if cfg.default_provider == "mock" else DEFAULT_MODEL
        mock = MockProvider(model_id=mock_model_id)
        engine.providers.register_provider_models(mock, engine.models)

        # Register OpenAI adapter when keyed or explicitly selected as default.
        if cfg.openai_configured or cfg.default_provider == "openai":
            openai = OpenAICompatibleProvider(
                api_key=cfg.openai_api_key,
                base_url=cfg.openai_base_url,
                model_id=cfg.openai_model,
                timeout_seconds=cfg.openai_timeout_seconds,
                max_retries=cfg.openai_max_retries,
            )
            engine.providers.register_provider_models(openai, engine.models)

        return engine

    def complete(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        *,
        cancel_event: threading.Event | None = None,
        delay_ms: int = 0,
        fail: bool = False,
        policy: RoutingPolicy | None = None,
        preferred_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> InferenceResult:
        """Route then generate; raises CialError or InferenceCancelledError."""
        t0 = time.perf_counter()
        route_policy = policy or self.config.routing_policy
        preferred = self._resolve_preferred_model(preferred_model_id)

        if route_policy == RoutingPolicy.MANUAL:
            request = RoutingRequest(
                policy=RoutingPolicy.MANUAL,
                manual_provider_id=self.config.default_provider,
                manual_model_id=preferred,
            )
        else:
            request = RoutingRequest(
                policy=route_policy,
                preferred_model_id=preferred,
            )

        try:
            decision = self.router.route(request)
            provider = self.providers.get(decision.provider_id)
            gen_req = GenerateRequest(
                messages=messages,
                max_tokens=max_tokens,
                model_id=decision.model_id,
                cancel_event=cancel_event,
                delay_ms=delay_ms,
                fail=fail,
                metadata=dict(metadata or {}),
            )
            result = provider.generate(gen_req)
        except InferenceCancelledError:
            raise
        except CialError:
            raise

        elapsed = max(0, int(round((time.perf_counter() - t0) * 1000)))
        result.cial_provider_id = decision.provider_id
        result.cial_model_id = decision.model_id
        result.cial_routing_policy = decision.policy.value
        result.cial_route_reason = decision.reason
        result.cial_latency_ms = elapsed
        result.cial_fallback_count = decision.fallback_count
        result.cial_health_state = decision.health_state.value
        return result

    def _resolve_preferred_model(self, preferred_model_id: str | None) -> str:
        """
        Select internal CIAL model id.

        When ``CIAL_PROVIDER=openai``, prefer the OpenAI model even if Protocol
        V1 wire model is still ``cobra-core-qwen3-8b``.
        """
        if self.config.default_provider == "openai":
            return self.config.openai_model
        return preferred_model_id or self.config.default_model

    def complete_as_protocol(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        *,
        cancel_event: threading.Event | None = None,
        delay_ms: int = 0,
        fail: bool = False,
    ) -> ProtoResult:
        """
        Generate and return Protocol V1 InferenceResult (content/tokens/ms only).

        Maps CialError → InferenceFailedError for InferenceService.
        """
        try:
            result = self.complete(
                messages,
                max_tokens,
                cancel_event=cancel_event,
                delay_ms=delay_ms,
                fail=fail,
            )
        except InferenceCancelledError:
            raise
        except CialError as exc:
            raise to_inference_failed(exc) from None

        return ProtoResult(
            content=result.content,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            inference_ms=result.inference_ms,
        )
