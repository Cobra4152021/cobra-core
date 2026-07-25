"""Server configuration from environment (no secrets logged or echoed)."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from cobra_core.protocol_v1.constants import (
    COMPATIBILITY_VERSION,
    DEFAULT_MODEL,
    PROTOCOL_VERSION,
)


class ConfigError(ValueError):
    """Raised for invalid/unsupported protocol configuration."""


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a positive integer") from exc
    if n <= 0:
        raise ConfigError(f"{name} must be a positive integer")
    return n


def _env_optional_int(name: str) -> int | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a positive integer") from exc
    if n <= 0:
        raise ConfigError(f"{name} must be a positive integer")
    return n


def _env_nonneg_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a non-negative integer") from exc
    if n < 0:
        raise ConfigError(f"{name} must be a non-negative integer")
    return n


def resolve_git_sha() -> str:
    explicit = os.environ.get("COBRA_CORE_GIT_SHA", "").strip()
    if explicit:
        return explicit
    try:
        root = Path(__file__).resolve().parents[3]
        out = subprocess.run(
            ["git", "-c", f"safe.directory={root}", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        sha = (out.stdout or "").strip()
        if sha and out.returncode == 0:
            return sha
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        raw = os.environ.get(name, "").strip()
        if raw:
            return raw
    return default


@dataclass(frozen=True)
class ServerConfig:
    auth_secret: str
    model: str
    revision: str
    git_sha: str
    max_context: int | None
    max_output_tokens: int | None
    timeout_ms: int
    host: str
    port: int
    inference_mode: str
    log_level: str
    protocol_version: str
    compatibility_version: str
    mock_delay_ms: int
    eager_load: bool
    # RC1 process controls (server-local; not Protocol schema fields).
    enabled: bool
    max_concurrent: int
    daily_request_limit: int | None
    metrics_enabled: bool

    @property
    def auth_configured(self) -> bool:
        return bool(self.auth_secret)


def load_config() -> ServerConfig:
    """
    Load config from environment.

    Required for serving: COBRA_CORE_AUTH_SECRET (enforced by CLI / make_server).
    Protocol/compat env overrides must equal frozen V1 values when set.
    """
    proto = _first_env("COBRA_PROTOCOL_VERSION", default=PROTOCOL_VERSION)
    compat = _first_env("COBRA_COMPATIBILITY_VERSION", default=COMPATIBILITY_VERSION)
    if proto != PROTOCOL_VERSION:
        raise ConfigError(
            f"unsupported COBRA_PROTOCOL_VERSION={proto!r}; only {PROTOCOL_VERSION!r} allowed"
        )
    if compat != COMPATIBILITY_VERSION:
        raise ConfigError(
            f"unsupported COBRA_COMPATIBILITY_VERSION={compat!r}; "
            f"only {COMPATIBILITY_VERSION!r} allowed"
        )

    secret = os.environ.get("COBRA_CORE_AUTH_SECRET", "").strip()
    revision = os.environ.get("COBRA_CORE_REVISION", "").strip()
    git_sha = resolve_git_sha()
    if not revision:
        revision = git_sha[:12] if git_sha else "local-dev"

    mode = os.environ.get("COBRA_INFERENCE_MODE", "mock").strip().lower() or "mock"
    if mode not in {"mock", "echo", "test", "local", "qwen-local"}:
        raise ConfigError(
            "COBRA_INFERENCE_MODE must be one of: mock, echo, test, local, qwen-local"
        )

    host = _first_env("COBRA_CORE_HOST", "COBRA_PROTOCOL_HOST", default="127.0.0.1")
    port_raw = (
        os.environ.get("COBRA_CORE_PORT", "").strip()
        or os.environ.get("COBRA_PROTOCOL_PORT", "").strip()
    )
    if port_raw:
        try:
            port = int(port_raw)
        except ValueError as exc:
            raise ConfigError("COBRA_CORE_PORT must be a positive integer") from exc
        if port <= 0:
            raise ConfigError("COBRA_CORE_PORT must be a positive integer")
    else:
        port = 8080

    log_level = (os.environ.get("COBRA_CORE_LOG_LEVEL", "INFO").strip() or "INFO").upper()
    eager = os.environ.get("COBRA_CORE_EAGER_LOAD", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    # Kill switch: default enabled when secret present; explicit false disables completions.
    enabled_raw = os.environ.get("COBRA_CORE_ENABLED", "true").strip().lower()
    enabled = enabled_raw not in {"0", "false", "no", "off"}
    metrics = os.environ.get("COBRA_CORE_METRICS_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }

    return ServerConfig(
        auth_secret=secret,
        model=(os.environ.get("COBRA_CORE_MODEL", "").strip() or DEFAULT_MODEL),
        revision=revision,
        git_sha=git_sha or revision,
        max_context=_env_optional_int("COBRA_CORE_MAX_CONTEXT"),
        max_output_tokens=_env_optional_int("COBRA_CORE_MAX_OUTPUT_TOKENS"),
        timeout_ms=_env_int("COBRA_CORE_TIMEOUT_MS", 120_000),
        host=host,
        port=port,
        inference_mode=mode,
        log_level=log_level,
        protocol_version=proto,
        compatibility_version=compat,
        mock_delay_ms=_env_nonneg_int("COBRA_INFERENCE_MOCK_DELAY_MS", 0),
        eager_load=eager,
        enabled=enabled,
        max_concurrent=_env_int("COBRA_CORE_MAX_CONCURRENT", 1),
        daily_request_limit=_env_optional_int("COBRA_CORE_DAILY_REQUEST_LIMIT"),
        metrics_enabled=metrics,
    )
