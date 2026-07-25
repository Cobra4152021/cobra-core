"""
AIR routing policy configuration (human-governed; no code changes for knobs).

Loaded from env / optional JSON. Does not self-learn.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AirPolicyConfig:
    """
    Deterministic routing policy knobs.

    Order is fixed by AdaptiveRouter (capabilities → health → policy → cost →
    latency → tiebreak). This config only tunes preference weights / exclusions.
    """

    policy_id: str = "default_v1"
    # When profile requires live and a live candidate exists, drop offline models.
    prefer_live_when_required: bool = True
    # Exclude degraded models unless no healthier candidate remains.
    prefer_healthy_over_degraded: bool = True
    # Operator soft preferences: provider_id → lower is preferred (stable).
    provider_preference: dict[str, int] = field(default_factory=dict)
    # Hard exclusions (never select), even if capability-matched.
    excluded_providers: frozenset[str] = field(default_factory=frozenset)
    excluded_models: frozenset[tuple[str, str]] = field(default_factory=frozenset)
    metadata: dict[str, Any] = field(default_factory=dict)


def default_air_policy() -> AirPolicyConfig:
    return AirPolicyConfig(
        provider_preference={"openai": 10, "mock": 50},
    )


def load_air_policy_from_dict(data: dict[str, Any]) -> AirPolicyConfig:
    """Parse a policy document (JSON-compatible dict)."""
    prefs_raw = data.get("provider_preference") or {}
    prefs = {str(k): int(v) for k, v in prefs_raw.items()}
    excluded_providers = frozenset(
        str(x).strip().lower() for x in (data.get("excluded_providers") or [])
    )
    excluded_models: set[tuple[str, str]] = set()
    for item in data.get("excluded_models") or []:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            excluded_models.add((str(item[0]), str(item[1])))
        elif isinstance(item, str) and "/" in item:
            p, m = item.split("/", 1)
            excluded_models.add((p.strip(), m.strip()))
    return AirPolicyConfig(
        policy_id=str(data.get("policy_id") or "default_v1"),
        prefer_live_when_required=bool(data.get("prefer_live_when_required", True)),
        prefer_healthy_over_degraded=bool(data.get("prefer_healthy_over_degraded", True)),
        provider_preference=prefs,
        excluded_providers=excluded_providers,
        excluded_models=frozenset(excluded_models),
        metadata=dict(data.get("metadata") or {}),
    )


def load_air_policy(*, path: str | Path | None = None) -> AirPolicyConfig:
    """
    Load policy from AIR_POLICY_PATH JSON, else defaults + env overlays.

    Env overlays (optional):
      AIR_POLICY_ID
      AIR_EXCLUDE_PROVIDERS=comma,separated
    """
    policy_path = path or os.environ.get("AIR_POLICY_PATH", "").strip() or None
    if policy_path:
        raw = Path(policy_path).read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("AIR policy file must be a JSON object")
        base = load_air_policy_from_dict(data)
    else:
        base = default_air_policy()

    policy_id = os.environ.get("AIR_POLICY_ID", "").strip() or base.policy_id
    excluded = set(base.excluded_providers)
    extra = os.environ.get("AIR_EXCLUDE_PROVIDERS", "").strip()
    if extra:
        excluded |= {p.strip().lower() for p in extra.split(",") if p.strip()}

    return AirPolicyConfig(
        policy_id=policy_id,
        prefer_live_when_required=base.prefer_live_when_required,
        prefer_healthy_over_degraded=base.prefer_healthy_over_degraded,
        provider_preference=dict(base.provider_preference),
        excluded_providers=frozenset(excluded),
        excluded_models=base.excluded_models,
        metadata=dict(base.metadata),
    )
