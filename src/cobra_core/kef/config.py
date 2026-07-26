"""KEF configuration (env). Invalid values fail closed at load."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() not in {"0", "false", "no", "off"}


def _int(name: str, raw: str | None, default: int, *, min_v: int = 1, max_v: int = 10_000) -> int:
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw).strip())
    except ValueError as exc:
        raise ValueError(f"invalid {name}: {raw!r}") from exc
    if value < min_v or value > max_v:
        raise ValueError(f"{name} out of range [{min_v}, {max_v}]: {value}")
    return value


@dataclass(frozen=True)
class KefConfig:
    enabled: bool = True
    max_results: int = 25
    default_connector: str = "memory"
    allow_request_seed: bool = True  # normalize Computer EvidenceRefs into MemoryConnector
    require_integrity_hash: bool = False
    semantic_enabled: bool = False  # out of scope — embeddings disabled

    def __post_init__(self) -> None:
        if self.max_results < 1:
            raise ValueError("max_results must be >= 1")
        if self.semantic_enabled:
            raise ValueError("semantic search is out of scope for KC-027")


def load_kef_config(*, env: dict[str, str] | None = None) -> KefConfig:
    e = env if env is not None else os.environ
    return KefConfig(
        enabled=_bool(e.get("KEF_ENABLED"), True),
        max_results=_int("KEF_MAX_RESULTS", e.get("KEF_MAX_RESULTS"), 25, min_v=1, max_v=500),
        default_connector=(e.get("KEF_DEFAULT_CONNECTOR") or "memory").strip().lower() or "memory",
        allow_request_seed=_bool(e.get("KEF_ALLOW_REQUEST_SEED"), True),
        require_integrity_hash=_bool(e.get("KEF_REQUIRE_INTEGRITY_HASH"), False),
        semantic_enabled=_bool(e.get("KEF_SEMANTIC_ENABLED"), False),
    )


def kef_enabled(*, env: dict[str, str] | None = None) -> bool:
    return load_kef_config(env=env).enabled
