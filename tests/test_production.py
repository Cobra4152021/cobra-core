"""KC-037 Production Readiness & Hardening Framework tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.production.audit import PRODUCTION_AUDIT
from cobra_core.production.backup import BACKUP
from cobra_core.production.configuration import validate_configuration
from cobra_core.production.deployment import run_local_validation_phase
from cobra_core.production.healthcheck import health_bundle, liveness, readiness
from cobra_core.production.http_api import (
    handle_production_health,
    handle_production_security_review,
    handle_production_startup_report,
    handle_production_status,
)
from cobra_core.production.integrity import integrity_report
from cobra_core.production.loadtest import run_load_test, run_standard_suite
from cobra_core.production.metrics import PRODUCTION_METRICS
from cobra_core.production.migrations import MIGRATIONS
from cobra_core.production.restore import RESTORE, RestoreError
from cobra_core.production.security_review import run_security_review
from cobra_core.production.startup import run_startup_validation, startup_ok


@pytest.fixture(autouse=True)
def _reset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "prhf-test-secret-value-32chars!!")
    monkeypatch.delenv("COBRA_CORE_PRODUCTION", raising=False)
    monkeypatch.delenv("PRODUCTION_ENABLED", raising=False)
    monkeypatch.delenv("COBRA_CORE_DEBUG", raising=False)
    PRODUCTION_METRICS.clear()
    PRODUCTION_AUDIT.clear()
    MIGRATIONS.reset_for_tests()
    BACKUP.reset_for_tests(root=tmp_path / "backups")
    yield
    PRODUCTION_METRICS.clear()
    PRODUCTION_AUDIT.clear()
    MIGRATIONS.reset_for_tests()


def test_startup_validation_ok(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "prhf-test-secret-value-32chars!!")
    report = run_startup_validation(correlation_id="t1")
    assert report.ok is True
    assert report.aborted is False
    assert startup_ok() is True
    assert report.checks["organization_registry"] is True
    body = handle_production_startup_report()
    assert body["ok"] is True


def test_startup_aborts_on_missing_secret():
    env = {
        "PRHF_ABORT_ON_CRITICAL": "true",
        "PRHF_REQUIRE_AUTH_SECRET": "true",
    }
    report = run_startup_validation(env=env, correlation_id="abort")
    assert report.aborted is True
    assert any(f.code == "missing_secret" for f in report.findings)


def test_configuration_unsafe_production_flag(monkeypatch: pytest.MonkeyPatch):
    env = {
        "COBRA_CORE_AUTH_SECRET": "prhf-test-secret-value-32chars!!",
        "COBRA_CORE_PRODUCTION": "true",
    }
    findings = validate_configuration(env)
    assert any(f.code == "production_flag_set" for f in findings)


def test_migration_dry_run_apply_rollback():
    dry = MIGRATIONS.dry_run()
    assert dry["dry_run"] is True
    assert "m001_motf_registry" in dry["pending"]
    assert MIGRATIONS.apply("m001_motf_registry")["ok"] is True
    assert "m001_motf_registry" in MIGRATIONS.applied()
    assert MIGRATIONS.rollback("m001_motf_registry")["ok"] is True
    assert "m001_motf_registry" not in MIGRATIONS.applied()


def test_backup_and_restore(tmp_path: Path):
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
    from cobra_core.organizations.tenancy import TENANCY
    from cobra_core.security.identity import IDENTITY
    from cobra_core.security.roles import ROLE_REGISTRY
    from cobra_core.security.schemas import BuiltInRole

    TENANCY.reset_for_tests()
    ROLE_REGISTRY.reset_for_tests()
    IDENTITY.reset_for_tests()
    IDENTITY.bootstrap()
    owner = IDENTITY.create_user(
        display_name="P",
        roles=[BuiltInRole.ADMINISTRATOR.value],
        principal_id="user_prhf",
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="PRHF Org",
        owner=owner.principal_id,
        organization_id="org_prhf",
        seed_departments=False,
    )
    art = BACKUP.create(actor="test")
    assert Path(art.path).is_file()
    payload = json.loads(Path(art.path).read_text(encoding="utf-8"))
    assert payload["vault_objects_included"] is False
    assert payload["format"] == "prhf_backup_v1"
    dry = RESTORE.restore_file(art.path, dry_run=True)
    assert dry["dry_run"] is True
    applied = RESTORE.restore_file(art.path, dry_run=False)
    assert applied["applied"] is True
    snap = PRODUCTION_METRICS.snapshot()
    assert snap["backup_success"] >= 1
    assert snap["restore_success"] >= 1


def test_restore_rejects_vault_bodies(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps(
            {
                "format": "prhf_backup_v1",
                "vault_objects_included": True,
                "organizations": [],
                "integrity": {},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RestoreError) as exc:
        RESTORE.restore_file(bad)
    assert exc.value.code == "incompatible"


def test_health_model():
    assert liveness()["mode"] == "live"
    ready = readiness(startup_ok=True)
    assert ready["mode"] in {"ready", "degraded", "maintenance", "not_ready"}
    bundle = health_bundle(startup_ok=True)
    assert "liveness" in bundle and "dependencies" in bundle
    assert handle_production_health()["ok"] is True


def test_integrity_and_security_review():
    report = integrity_report()
    assert report["openapi_checksum"]
    assert report["policy_checksum"]
    sec = run_security_review()
    assert sec["ok"] is True
    ids = {c["id"] for c in sec["checks"]}
    for required in {
        "default_deny",
        "no_credential_logging",
        "bearer_validation",
        "plugin_validation",
        "cross_org_isolation",
        "openapi_exposure",
        "debug_endpoints_disabled",
        "production_disabled",
    }:
        assert required in ids
    assert handle_production_security_review()["ok"] is True


def test_load_test_100_500_1000():
    r100 = run_load_test(100)
    assert r100["ok"] is True
    assert r100["requests"] == 100
    assert r100["errors"] == 0
    assert r100["latency_ms"]["avg"] >= 0
    suite = run_standard_suite()
    assert suite["ok"] is True
    assert suite["sizes"]["500"]["requests"] == 500
    assert suite["sizes"]["1000"]["requests"] == 1000


def test_deployment_phase1_and_status():
    phase = run_local_validation_phase()
    assert phase["phase"] == "phase_1_local_validation"
    st = handle_production_status()
    assert st["production_enabled"] is False
    assert len(st["certification_phases"]) == 8


def test_audit_events():
    run_startup_validation(correlation_id="audit")
    MIGRATIONS.dry_run()
    events = {e["event"] for e in PRODUCTION_AUDIT.recent(limit=50)}
    assert "startup" in events
    assert "migration_dry_run" in events


def test_regression_kc_021_through_036():
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
    resp = handle_public_api(
        method="GET",
        path="/api/v1/status",
        authenticated=True,
        request_id="prhf_reg",
    )
    assert resp.status == 200
    assert run_startup_validation().ok is True
