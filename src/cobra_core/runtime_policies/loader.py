"""Runtime policy profile loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = ROOT / "runtime_policies" / "registry.json"


class ResourceGuard(BaseModel):
    model_config = ConfigDict(extra="allow")

    require_free_vram_gb: float | None = None
    abort_on_access_violation: bool = True


class RuntimePolicyProfile(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    profile_id: str
    version: str
    max_input_tokens: int = Field(ge=1)
    max_output_tokens: int = Field(ge=1)
    temperature: float = Field(ge=0.0, le=2.0)
    top_p: float | None = None
    top_k: int | None = None
    seed_policy: str
    seed: int | None = None
    thinking_policy: str
    repetition_controls: str
    timeout_seconds: int = Field(ge=1)
    retry_policy: str
    output_parser: str
    evidence_prompt_standard: str
    resource_guard: ResourceGuard = Field(default_factory=ResourceGuard)
    notes: str | None = None


class RuntimePolicyError(Exception):
    pass


def load_runtime_registry(path: Path | str | None = None) -> dict[str, Any]:
    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY
    if not registry_path.is_file():
        raise RuntimePolicyError(f"Missing runtime registry: {registry_path}")
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], data)


def load_runtime_profile(
    profile_id: str,
    *,
    repo_root: Path | None = None,
) -> RuntimePolicyProfile:
    root = repo_root or ROOT
    registry = load_runtime_registry(root / "runtime_policies" / "registry.json")
    profiles = registry.get("profiles", {})
    if profile_id not in profiles:
        raise RuntimePolicyError(f"Unknown runtime profile: {profile_id}")
    rel = profiles[profile_id]
    path = root / rel
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimePolicyError(f"Invalid profile: {path}")
    return RuntimePolicyProfile.model_validate(data)


def validate_runtime_registry(*, repo_root: Path | None = None) -> list[str]:
    root = repo_root or ROOT
    registry = load_runtime_registry(root / "runtime_policies" / "registry.json")
    errors: list[str] = []
    for pid, rel in registry.get("profiles", {}).items():
        path = root / rel
        if not path.is_file():
            errors.append(f"missing profile {pid}: {rel}")
            continue
        try:
            load_runtime_profile(pid, repo_root=root)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{pid}: {exc}")
    return errors
