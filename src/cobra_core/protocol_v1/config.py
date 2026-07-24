"""Server configuration from environment (no secrets logged)."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        return default
    return n if n > 0 else default


def _env_optional_int(name: str) -> int | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    return n if n > 0 else None


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

    @property
    def auth_configured(self) -> bool:
        return bool(self.auth_secret)


def load_config() -> ServerConfig:
    from cobra_core.protocol_v1.constants import DEFAULT_MODEL

    secret = os.environ.get("COBRA_CORE_AUTH_SECRET", "").strip()
    revision = os.environ.get("COBRA_CORE_REVISION", "").strip()
    git_sha = resolve_git_sha()
    if not revision:
        revision = git_sha[:12] if git_sha else "local-dev"
    mode = os.environ.get("COBRA_INFERENCE_MODE", "mock").strip().lower() or "mock"
    return ServerConfig(
        auth_secret=secret,
        model=(os.environ.get("COBRA_CORE_MODEL", "").strip() or DEFAULT_MODEL),
        revision=revision,
        git_sha=git_sha or revision,
        max_context=_env_optional_int("COBRA_CORE_MAX_CONTEXT"),
        max_output_tokens=_env_optional_int("COBRA_CORE_MAX_OUTPUT_TOKENS"),
        timeout_ms=_env_int("COBRA_CORE_TIMEOUT_MS", 120_000),
        host=os.environ.get("COBRA_PROTOCOL_HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_env_int("COBRA_PROTOCOL_PORT", 8080),
        inference_mode=mode,
    )
