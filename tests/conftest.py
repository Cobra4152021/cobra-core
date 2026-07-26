"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _kef_unit_test_defaults(monkeypatch: pytest.MonkeyPatch):
    """
    Unit tests historically inject EvidenceRefs without a live Vault.

    Staging/production defaults keep KEF_ALLOW_REQUEST_SEED=false; enable seed
    only for the pytest process unless a test overrides env/config.
    """
    monkeypatch.setenv("KEF_ALLOW_REQUEST_SEED", "true")
    monkeypatch.setenv("KEF_EVIDENCE_VAULT_ENABLED", "false")
    try:
        from cobra_core.kef.config import load_kef_config
        from cobra_core.kef.retrieval import KEF_GATEWAY

        previous = KEF_GATEWAY.config
        KEF_GATEWAY.config = load_kef_config()
        yield
        KEF_GATEWAY.config = previous
    except Exception:
        yield


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def cases_dir(repo_root: Path) -> Path:
    return repo_root / "benchmarks" / "cases"


@pytest.fixture
def primary_qwen_manifest_path(repo_root: Path) -> Path:
    return repo_root / "model-cards" / "qwen" / "qwen3-32b.manifest.json"
