"""KC-038 Release Candidate 1 certification suite (feature freeze)."""

from __future__ import annotations

import pytest

from cobra_core.release.freeze import freeze_manifest
from cobra_core.release.rc1 import RC1_VERSION, run_rc1_certification
from cobra_core.release.soak import staging_24h_status


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "rc1-cert-secret-value-32chars!!!!")
    monkeypatch.delenv("COBRA_CORE_PRODUCTION", raising=False)
    monkeypatch.delenv("COBRA_CORE_DEBUG", raising=False)


def test_freeze_manifest_locks_surfaces():
    m = freeze_manifest()
    assert m["version"] == RC1_VERSION
    assert m["production_enabled"] is False
    assert "public_api_v1" in m["frozen_surfaces"]
    assert m["checksums"]["openapi"]


def test_rc1_certification_pack_offline():
    # Short local soak; 24h staging remains blocking by design.
    report = run_rc1_certification(local_soak_s=5.0)
    assert report["version"] == RC1_VERSION
    assert report["feature_freeze"] is True
    assert report["production_enabled"] is False
    assert report["offline_certification_ok"] is True
    assert report["phases"]["api_compatibility"]["ok"] is True
    assert report["phases"]["plugin_compatibility"]["ok"] is True
    assert report["phases"]["security"]["ok"] is True
    assert report["phases"]["recovery"]["ok"] is True
    assert report["phases"]["performance"]["ok"] is True
    assert report["phases"]["benchmark"]["ok"] is True
    assert report["phases"]["local_soak"]["ok"] is True
    assert "5000" in report["phases"]["performance"]["sizes"]
    assert report["phases"]["performance"]["sizes"]["5000"]["ok"] is True
    # Exit gate: 24h soak incomplete → not approved
    assert report["release_candidate_approved"] is False
    assert "phase_7_soak_24h_incomplete" in report["blocking_issues"]
    assert report["verdict"].startswith("PARTIAL")


def test_staging_24h_explicitly_incomplete():
    st = staging_24h_status()
    assert st["complete"] is False
    assert st["blocking"] is True


def test_regression_matrix_kc021_through_037():
    """Import/smoke matrix covering King Cobra stack through PRHF."""
    from cobra_core.air import bridge as air_bridge
    from cobra_core.api.router import handle_public_api
    from cobra_core.benchmark.runner import BenchmarkRunner
    from cobra_core.cial.config import load_cial_config
    from cobra_core.isf.registry import SKILL_REGISTRY
    from cobra_core.kef.config import load_kef_config
    from cobra_core.operations.health import overall_status
    from cobra_core.operations.schemas import ComponentHealth
    from cobra_core.organizations.http_api import handle_organizations_list
    from cobra_core.plugins.manager import PLUGIN_MANAGER
    from cobra_core.production.security_review import run_security_review
    from cobra_core.production.startup import run_startup_validation
    from cobra_core.resilience.config import rrf_enabled
    from cobra_core.security.http_api import handle_security_status

    assert load_cial_config() is not None
    assert air_bridge is not None
    assert len(SKILL_REGISTRY) >= 1
    assert load_kef_config() is not None
    assert isinstance(rrf_enabled(), bool)
    assert overall_status() in set(ComponentHealth)
    assert BenchmarkRunner().run_dataset("policy_review_v1").overall_score >= 0.0
    PLUGIN_MANAGER.reset_for_tests()
    PLUGIN_MANAGER.bootstrap_samples()
    assert len(PLUGIN_MANAGER.list_plugins()) >= 4
    assert handle_security_status()["ok"] is True
    assert handle_organizations_list()["ok"] is True
    assert (
        handle_public_api(
            method="GET", path="/api/v1/health", authenticated=False, request_id="rc1"
        ).status
        == 200
    )
    assert run_security_review()["ok"] is True
    assert run_startup_validation(
        env={"COBRA_CORE_AUTH_SECRET": "rc1-cert-secret-value-32chars!!!!"}
    ).ok
