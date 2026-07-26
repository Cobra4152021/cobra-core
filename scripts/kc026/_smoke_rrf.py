#!/usr/bin/env python3
from cobra_core.air.capabilities import AirCapability
from cobra_core.air.catalog import build_default_catalog
from cobra_core.cial.config import CialConfig
from cobra_core.cial.types import RoutingPolicy
from cobra_core.protocol_v1.constants import DEFAULT_MODEL
from cobra_core.resilience.audit import RRF_AUDIT
from cobra_core.resilience.budget import GLOBAL_BUDGET
from cobra_core.resilience.config import ResilienceConfig
from cobra_core.resilience.executor import ResilienceExecutor
from cobra_core.resilience.faults import scripted_caller
from cobra_core.resilience.idempotency import IDEMPOTENCY_STORE
from cobra_core.resilience.metrics import RRF_METRICS
from cobra_core.resilience.types import ResilienceRequest, RouteTarget

print("imports ok", flush=True)
RRF_AUDIT.clear()
RRF_METRICS.reset()
IDEMPOTENCY_STORE.clear()
GLOBAL_BUDGET.reset()
cfg = ResilienceConfig(
    enabled=True,
    max_attempts=2,
    initial_backoff_ms=1,
    max_backoff_ms=5,
    request_deadline_ms=5000,
    jitter_seed=0,
)
caller = scripted_caller(["timeout", "success"])
print("caller ok", flush=True)
ex = ResilienceExecutor(
    cfg=cfg,
    provider_call=caller,
    catalog=build_default_catalog(openai_enabled=True),
    sleep_fn=lambda s: None,
    cial_config=CialConfig(
        enabled=True,
        active_profile="research",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=True,
        openai_api_key="k",
        openai_model="gpt-5.4-mini",
        mock_model=DEFAULT_MODEL,
    ),
)
print("executor ok", flush=True)
req = ResilienceRequest(
    execution_id="t1",
    correlation_id="c",
    skill_id="evidence_summary",
    skill_version="1.0.0",
    profile_id="default",
    required_capabilities=frozenset({AirCapability.SUMMARIZATION}),
    primary=RouteTarget("openai", "gpt-5.4-mini"),
    allow_offline_fallback=True,
)
print("exec", flush=True)
res = ex.execute(req, messages=[{"role": "user", "content": "x"}], max_tokens=32)
print(res.status, len(caller.calls), flush=True)
