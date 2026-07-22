"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def cases_dir(repo_root: Path) -> Path:
    return repo_root / "benchmarks" / "cases"


@pytest.fixture
def example_manifest_path(repo_root: Path) -> Path:
    return repo_root / "model-cards" / "EXAMPLE_qwen_manifest.json"
