"""Validation helpers for benchmark cases and model manifests."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from cobra_core.schemas.benchmark import BenchmarkCase
from cobra_core.schemas.manifest import ModelManifest


class ValidationIssue:
    """A single validation failure for reporting."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def load_json_model[T: BaseModel](path: Path, model_type: type[T]) -> T:
    """Load and validate a JSON file into a Pydantic model."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return model_type.model_validate(data)


def validate_benchmark_case_file(path: Path) -> tuple[BenchmarkCase | None, list[ValidationIssue]]:
    """Validate one benchmark case JSON file."""
    try:
        case = load_json_model(path, BenchmarkCase)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        return None, [ValidationIssue(path, str(exc))]
    return case, []


def validate_manifest_file(path: Path) -> tuple[ModelManifest | None, list[ValidationIssue]]:
    """Validate one model manifest JSON file."""
    try:
        manifest = load_json_model(path, ModelManifest)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        return None, [ValidationIssue(path, str(exc))]
    return manifest, []


def validate_json_dir[T: BaseModel](
    directory: Path,
    model_type: type[T],
    pattern: str = "*.json",
    *,
    recursive: bool = False,
) -> tuple[list[T], list[ValidationIssue]]:
    """Validate matching JSON files in a directory."""
    if not directory.is_dir():
        return [], [ValidationIssue(directory, "directory does not exist")]

    models: list[T] = []
    issues: list[ValidationIssue] = []
    files = sorted(directory.rglob(pattern) if recursive else directory.glob(pattern))
    files = [path for path in files if path.is_file() and not path.name.startswith(".")]
    if not files:
        issues.append(ValidationIssue(directory, f"no files matching {pattern}"))
        return models, issues

    for path in files:
        try:
            models.append(load_json_model(path, model_type))
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            issues.append(ValidationIssue(path, str(exc)))
    return models, issues
