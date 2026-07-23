"""Prompt template registry loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = ROOT / "prompts" / "registry.json"


class PromptTemplate(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    template_id: str
    version: str
    task_type: str
    system_prompt: str
    user_prompt_structure: str
    evidence_delimiter_standard: str
    output_schema: str
    intended_consumer: str
    strictness_level: str
    compatibility_notes: str
    benchmark_use_restrictions: str
    change_rationale: str


class PromptRegistryError(Exception):
    pass


def load_prompt_registry(path: Path | str | None = None) -> dict[str, Any]:
    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY
    if not registry_path.is_file():
        raise PromptRegistryError(f"Missing prompt registry: {registry_path}")
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], data)


def load_prompt_template(
    template_id: str,
    version: str,
    *,
    repo_root: Path | None = None,
) -> PromptTemplate:
    root = repo_root or ROOT
    registry = load_prompt_registry(root / "prompts" / "registry.json")
    templates = registry.get("templates", {})
    if template_id not in templates or version not in templates[template_id]:
        raise PromptRegistryError(f"Unknown template {template_id}@{version}")
    rel = templates[template_id][version]
    path = root / rel
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PromptRegistryError(f"Invalid template file: {path}")
    # Reject path-injection style fields
    for key, value in data.items():
        if isinstance(value, str) and ("../" in value or "..\\" in value):
            raise PromptRegistryError(f"Path traversal rejected in field {key}")
    return PromptTemplate.model_validate(data)


def validate_prompt_registry(*, repo_root: Path | None = None) -> list[str]:
    root = repo_root or ROOT
    registry = load_prompt_registry(root / "prompts" / "registry.json")
    errors: list[str] = []
    templates = registry.get("templates", {})
    for tid, versions in templates.items():
        for ver, rel in versions.items():
            path = root / rel
            if not path.is_file():
                errors.append(f"missing {tid}@{ver}: {rel}")
            else:
                try:
                    load_prompt_template(tid, ver, repo_root=root)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{tid}@{ver}: {exc}")
    return errors
