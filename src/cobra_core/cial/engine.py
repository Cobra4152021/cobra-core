"""CIAL engine: route + generate through registered providers."""

from __future__ import annotations

import threading
import time
from typing import Any

from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.errors import CialError, CialErrorCode, to_inference_failed
from cobra_core.cial.guards import LiveRequestGuard
from cobra_core.cial.providers.mock import MockProvider
from cobra_core.cial.providers.openai_compatible import OpenAICompatibleProvider
from cobra_core.cial.registry import ModelRegistry, ProviderRegistry
from cobra_core.cial.router import DeterministicRouter
from cobra_core.cial.types import (
    GenerateRequest,
    InferenceResult,
    ModelRecord,
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

    Live OpenAI-compatible use is opt-in via ``CIAL_LIVE_PROVIDER_ENABLED``
    and only on staging. Mock remains the safe default / rollback path.
    """

    def __init__(
        self,
        *,
        config: CialConfig | None = None,
        providers: ProviderRegistry | None = None,
        models: ModelRegistry | None = None,
        router: DeterministicRouter | None = None,
        live_guard: LiveRequestGuard | None = None,
    ) -> None:
        self.config = config or load_cial_config()
        self.providers = providers or ProviderRegistry()
        self.models = models or ModelRegistry()
        self.router = router or DeterministicRouter(self.models)
        self.live_guard = live_guard or LiveRequestGuard(self.config)

    @classmethod
    def build_default(cls, config: CialConfig | None = None) -> CialEngine:
        """Construct engine with mock always registered; openai only when live-ready."""
        cfg = config or load_cial_config()
        engine = cls(config=cfg)
        profile = cfg.resolved_profile()
        mock_model_id = cfg.mock_model or DEFAULT_MODEL
        mock = MockProvider(model_id=mock_model_id)
        engine.providers.register_provider_models(mock, engine.models)

        if cfg.can_use_live_provider and profile.provider_id == "openai":
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
        preferred, effective_provider, forced_mock = self._resolve_route_target(preferred_model_id)

        if route_policy == RoutingPolicy.MANUAL:
            request = RoutingRequest(
                policy=RoutingPolicy.MANUAL,
                manual_provider_id=effective_provider,
                manual_model_id=(
                    self.config.openai_model if effective_provider == "openai" else preferred
                ),
            )
        else:
            request = RoutingRequest(
                policy=route_policy,
                preferred_model_id=preferred,
            )

        acquired = False
        model: ModelRecord | None = None
        decision = None
        result: InferenceResult | None = None
        try:
            decision = self.router.route(request)
            if decision.provider_id == "openai" and not self.config.can_use_live_provider:
                raise CialError(
                    CialErrorCode.LIVE_PROVIDER_DISABLED,
                    "live provider is not enabled for this environment",
                )
            provider = self.providers.get(decision.provider_id)
            model = self.models.get(decision.provider_id, decision.model_id)
            if decision.provider_id == "openai":
                input_chars = sum(len(str(m.get("content") or "")) for m in messages)
                self.live_guard.acquire(
                    input_chars=input_chars,
                    max_tokens=max_tokens,
                    model=model,
                )
                acquired = True

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
        finally:
            if acquired and model is not None:
                prompt_tokens = result.prompt_tokens if result is not None else 0
                completion_tokens = result.completion_tokens if result is not None else 0
                self.live_guard.release(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=model,
                )

        assert decision is not None and result is not None
        elapsed = max(0, int(round((time.perf_counter() - t0) * 1000)))
        profile = self.config.resolved_profile()
        result.cial_provider_id = decision.provider_id
        result.cial_model_id = decision.model_id
        result.cial_profile = profile.profile_id
        result.cial_routing_policy = decision.policy.value
        result.cial_route_reason = (
            "profile_live_unavailable_use_offline" if forced_mock else decision.reason
        )
        result.cial_latency_ms = elapsed
        result.cial_fallback_count = decision.fallback_count
        result.cial_health_state = decision.health_state.value
        return result

    def _resolve_route_target(self, preferred_model_id: str | None) -> tuple[str, str, bool]:
        """
        Return (preferred_model_id, effective_provider, forced_offline).

        Profiles that require live (e.g. research) fall back to mock/offline when
        the live gate is closed — never silently activate a vendor.
        """
        profile = self.config.resolved_profile()
        if self.config.can_use_live_provider:
            return profile.model_id, profile.provider_id, False
        preferred = preferred_model_id or self.config.mock_model or DEFAULT_MODEL
        forced = profile.requires_live
        return preferred, "mock", forced

    def complete_as_protocol(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        *,
        cancel_event: threading.Event | None = None,
        delay_ms: int = 0,
        fail: bool = False,
    ) -> ProtoResult:
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
