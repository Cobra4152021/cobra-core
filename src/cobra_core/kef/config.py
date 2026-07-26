"""KEF configuration (env). Invalid values fail closed at load."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


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
    allow_request_seed: bool = False
    require_integrity_hash: bool = False
    semantic_enabled: bool = False  # out of scope — embeddings disabled
    vault_enabled: bool = False
    vault_base_url: str = ""
    vault_auth_token: str = ""
    vault_timeout_ms: int = 10_000
    vault_max_results: int = 25
    vault_max_content_bytes: int = 65_536
    vault_require_tls: bool = True
    vault_allow_private_hosts: bool = False
    vault_health_ttl_seconds: int = 30
    max_chunks_per_item: int = 8
    max_chars_per_chunk: int = 2_000
    max_total_evidence_chars: int = 24_000
    max_total_evidence_tokens: int = 6_000
    max_item_size_bytes: int = 65_536
    allow_unverified_integrity: bool = False
    vault_max_attempts: int = 2
    vault_circuit_failure_threshold: int = 5
    vault_circuit_window_seconds: int = 60
    vault_circuit_open_seconds: int = 30

    def __post_init__(self) -> None:
        if self.max_results < 1:
            raise ValueError("max_results must be >= 1")
        if self.semantic_enabled:
            raise ValueError("semantic search is out of scope for KC-027")
        if self.vault_enabled:
            parsed = urlparse(self.vault_base_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("KEF_EVIDENCE_VAULT_BASE_URL is required when vault is enabled")
            if self.vault_require_tls and parsed.scheme != "https":
                raise ValueError("Evidence Vault URL must use https")
            if not self.vault_auth_token:
                raise ValueError("KEF_EVIDENCE_VAULT_AUTH_TOKEN is required when vault is enabled")
        if self.max_total_evidence_chars < 1 or self.max_total_evidence_tokens < 1:
            raise ValueError("evidence context budgets must be positive")


def load_kef_config(*, env: dict[str, str] | None = None) -> KefConfig:
    e = env if env is not None else os.environ
    return KefConfig(
        enabled=_bool(e.get("KEF_ENABLED"), True),
        max_results=_int("KEF_MAX_RESULTS", e.get("KEF_MAX_RESULTS"), 25, min_v=1, max_v=500),
        default_connector=(e.get("KEF_DEFAULT_CONNECTOR") or "memory").strip().lower() or "memory",
        allow_request_seed=_bool(e.get("KEF_ALLOW_REQUEST_SEED"), False),
        require_integrity_hash=_bool(e.get("KEF_REQUIRE_INTEGRITY_HASH"), False),
        semantic_enabled=_bool(e.get("KEF_SEMANTIC_ENABLED"), False),
        vault_enabled=_bool(e.get("KEF_EVIDENCE_VAULT_ENABLED"), False),
        vault_base_url=(e.get("KEF_EVIDENCE_VAULT_BASE_URL") or "").strip().rstrip("/"),
        vault_auth_token=(e.get("KEF_EVIDENCE_VAULT_AUTH_TOKEN") or "").strip(),
        vault_timeout_ms=_int(
            "KEF_EVIDENCE_VAULT_TIMEOUT_MS",
            e.get("KEF_EVIDENCE_VAULT_TIMEOUT_MS"),
            10_000,
            max_v=300_000,
        ),
        vault_max_results=_int(
            "KEF_EVIDENCE_VAULT_MAX_RESULTS", e.get("KEF_EVIDENCE_VAULT_MAX_RESULTS"), 25, max_v=500
        ),
        vault_max_content_bytes=_int(
            "KEF_EVIDENCE_VAULT_MAX_CONTENT_BYTES",
            e.get("KEF_EVIDENCE_VAULT_MAX_CONTENT_BYTES"),
            65_536,
            max_v=10_000_000,
        ),
        vault_require_tls=_bool(e.get("KEF_EVIDENCE_VAULT_REQUIRE_TLS"), True),
        vault_allow_private_hosts=_bool(e.get("KEF_EVIDENCE_VAULT_ALLOW_PRIVATE_HOSTS"), False),
        vault_health_ttl_seconds=_int(
            "KEF_EVIDENCE_VAULT_HEALTH_TTL_SECONDS",
            e.get("KEF_EVIDENCE_VAULT_HEALTH_TTL_SECONDS"),
            30,
            max_v=3600,
        ),
        max_chunks_per_item=_int(
            "KEF_MAX_CHUNKS_PER_ITEM", e.get("KEF_MAX_CHUNKS_PER_ITEM"), 8, max_v=100
        ),
        max_chars_per_chunk=_int(
            "KEF_MAX_CHARS_PER_CHUNK", e.get("KEF_MAX_CHARS_PER_CHUNK"), 2_000, max_v=100_000
        ),
        max_total_evidence_chars=_int(
            "KEF_MAX_TOTAL_EVIDENCE_CHARS",
            e.get("KEF_MAX_TOTAL_EVIDENCE_CHARS"),
            24_000,
            max_v=10_000_000,
        ),
        max_total_evidence_tokens=_int(
            "KEF_MAX_TOTAL_EVIDENCE_TOKENS",
            e.get("KEF_MAX_TOTAL_EVIDENCE_TOKENS"),
            6_000,
            max_v=1_000_000,
        ),
        max_item_size_bytes=_int(
            "KEF_MAX_ITEM_SIZE_BYTES", e.get("KEF_MAX_ITEM_SIZE_BYTES"), 65_536, max_v=10_000_000
        ),
        allow_unverified_integrity=_bool(e.get("KEF_ALLOW_UNVERIFIED_INTEGRITY"), False),
        vault_max_attempts=_int(
            "KEF_EVIDENCE_VAULT_MAX_ATTEMPTS", e.get("KEF_EVIDENCE_VAULT_MAX_ATTEMPTS"), 2, max_v=2
        ),
        vault_circuit_failure_threshold=_int(
            "KEF_EVIDENCE_VAULT_CIRCUIT_FAILURE_THRESHOLD",
            e.get("KEF_EVIDENCE_VAULT_CIRCUIT_FAILURE_THRESHOLD"),
            5,
            max_v=100,
        ),
        vault_circuit_window_seconds=_int(
            "KEF_EVIDENCE_VAULT_CIRCUIT_WINDOW_SECONDS",
            e.get("KEF_EVIDENCE_VAULT_CIRCUIT_WINDOW_SECONDS"),
            60,
            max_v=3600,
        ),
        vault_circuit_open_seconds=_int(
            "KEF_EVIDENCE_VAULT_CIRCUIT_OPEN_SECONDS",
            e.get("KEF_EVIDENCE_VAULT_CIRCUIT_OPEN_SECONDS"),
            30,
            max_v=3600,
        ),
    )


def kef_enabled(*, env: dict[str, str] | None = None) -> bool:
    return load_kef_config(env=env).enabled
