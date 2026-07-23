"""Load and validate the evaluator registry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cobra_core.evaluators.metadata import EvaluatorMetadata

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = ROOT / "evaluators" / "registry.json"


class EvaluatorRegistryError(Exception):
    """Invalid evaluator registry or missing version."""


def configuration_hash(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_registry(path: Path | str | None = None) -> dict[str, object]:
    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY
    if not registry_path.is_file():
        raise EvaluatorRegistryError(f"Registry not found: {registry_path}")
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "evaluators" not in data:
        raise EvaluatorRegistryError("Registry must contain an 'evaluators' object")
    return data


def load_evaluator_metadata(
    evaluator_name: str,
    version: str,
    *,
    registry_path: Path | str | None = None,
    repo_root: Path | None = None,
) -> EvaluatorMetadata:
    root = repo_root or ROOT
    registry = load_registry(registry_path)
    evaluators = registry["evaluators"]
    assert isinstance(evaluators, dict)
    entry = evaluators.get(evaluator_name)
    if not isinstance(entry, dict):
        raise EvaluatorRegistryError(f"Unknown evaluator: {evaluator_name}")
    versions = entry.get("versions")
    if not isinstance(versions, dict) or version not in versions:
        raise EvaluatorRegistryError(f"Unknown version for {evaluator_name}: {version}")
    meta_rel = versions[version]
    if not isinstance(meta_rel, str):
        raise EvaluatorRegistryError("Version metadata path must be a string")
    meta_path = root / meta_rel
    if not meta_path.is_file():
        raise EvaluatorRegistryError(f"Metadata file missing: {meta_path}")
    return EvaluatorMetadata.model_validate_json(meta_path.read_text(encoding="utf-8"))


def list_evaluator_versions(
    *,
    registry_path: Path | str | None = None,
) -> dict[str, list[str]]:
    registry = load_registry(registry_path)
    evaluators = registry["evaluators"]
    assert isinstance(evaluators, dict)
    out: dict[str, list[str]] = {}
    for name, entry in evaluators.items():
        if isinstance(entry, dict) and isinstance(entry.get("versions"), dict):
            out[str(name)] = sorted(entry["versions"].keys())
    return out
