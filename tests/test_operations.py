"""KC-032 Operations Control Plane tests."""

from __future__ import annotations

import json

import pytest

from cobra_core.operations.alerts import alerts_public_dict, generate_alerts
from cobra_core.operations.audit import OPERATIONS_AUDIT
from cobra_core.operations.dashboard import dashboard_snapshot
from cobra_core.operations.feature_flags import FEATURE_FLAGS, read_only_mode, writes_allowed
from cobra_core.operations.health import (
    collect_health,
    health_public_dict,
    overall_status,
    reset_health_cache_for_tests,
)
from cobra_core.operations.http_api import (
    handle_operations_feature_flags,
    handle_operations_health,
    handle_operations_status,
)
from cobra_core.operations.maintenance import MAINTENANCE
from cobra_core.operations.metrics import OPERATIONS_METRICS
from cobra_core.operations.quotas import QUOTAS
from cobra_core.operations.schemas import ComponentHealth, QuotaTier
from cobra_core.operations.status import status_public_dict
from cobra_core.operations.usage import USAGE


@pytest.fixture(autouse=True)
def _reset_ocp():
    FEATURE_FLAGS.reset_for_tests()
    MAINTENANCE.reset_for_tests()
    QUOTAS.reset_for_tests()
    USAGE.reset_for_tests()
    OPERATIONS_METRICS.clear()
    OPERATIONS_AUDIT.clear()
    reset_health_cache_for_tests()
    yield
    FEATURE_FLAGS.reset_for_tests()
    MAINTENANCE.reset_for_tests()
    QUOTAS.reset_for_tests()
    USAGE.reset_for_tests()
    OPERATIONS_METRICS.clear()
    OPERATIONS_AUDIT.clear()
    reset_health_cache_for_tests()


def test_health_components_present():
    reports = collect_health()
    names = {r.component for r in reports}
    for required in {
        "computer",
        "cases",
        "workflows",
        "isf",
        "kef",
        "evidence_vault",
        "air",
        "rrf",
        "cial",
        "benchmark",
        "metrics",
        "audit",
    }:
        assert required in names
    body = health_public_dict()
    assert body["ok"] is True
    assert body["overall"] in {s.value for s in ComponentHealth}


def test_maintenance_mode_enter_exit():
    assert MAINTENANCE.allow_new_workflow() is True
    MAINTENANCE.enter(actor="ops", reason="patch window", reject_new_workflows=True)
    assert MAINTENANCE.state().active is True
    assert MAINTENANCE.allow_new_workflow() is False
    assert MAINTENANCE.allow_metrics() is True
    assert MAINTENANCE.allow_audit() is True
    health = health_public_dict()
    assert health["overall"] == ComponentHealth.MAINTENANCE.value
    MAINTENANCE.exit(actor="ops")
    assert MAINTENANCE.state().active is False
    events = [e for e in OPERATIONS_AUDIT.recent() if e["event"].startswith("maintenance_")]
    assert len(events) >= 2


def test_read_only_mode_denies_writes():
    assert read_only_mode() is False
    FEATURE_FLAGS.set_flag("READ_ONLY_MODE", True, actor="admin", reason="freeze")
    assert read_only_mode() is True
    assert writes_allowed() is False
    flag = FEATURE_FLAGS.get("READ_ONLY_MODE")
    assert flag.version >= 2
    entries = OPERATIONS_AUDIT.recent()
    assert any(e["event"] == "feature_flag_change" for e in entries)


def test_quota_warning_soft_hard():
    QUOTAS.set_hard_limit("cases_per_day", 10, actor="admin")
    # warning at 75% = 7, soft at 90% = 9
    assert QUOTAS.allow("cases_per_day", 1) is True
    for _ in range(7):
        QUOTAS.consume("cases_per_day")
    assert QUOTAS.usage("cases_per_day").tier == QuotaTier.WARNING
    QUOTAS.consume("cases_per_day")
    QUOTAS.consume("cases_per_day")
    assert QUOTAS.usage("cases_per_day").tier == QuotaTier.SOFT_LIMIT
    QUOTAS.consume("cases_per_day")
    assert QUOTAS.usage("cases_per_day").tier == QuotaTier.HARD_LIMIT
    assert QUOTAS.allow("cases_per_day", 1) is False
    assert OPERATIONS_METRICS.snapshot()["quota_exceeded"] >= 1


def test_feature_flags_registry_versioned():
    before = FEATURE_FLAGS.get("BENCHMARK_ENABLED")
    FEATURE_FLAGS.set_flag("BENCHMARK_ENABLED", not before.enabled, actor="admin")
    after = FEATURE_FLAGS.get("BENCHMARK_ENABLED")
    assert after.version == before.version + 1
    # no-op same value does not bump
    again = FEATURE_FLAGS.set_flag("BENCHMARK_ENABLED", after.enabled, actor="admin")
    assert again.version == after.version
    snap = handle_operations_feature_flags()
    assert snap["ok"] is True
    names = {f["name"] for f in snap["flags"]}
    assert "READ_ONLY_MODE" in names
    assert "LIVE_PROVIDER_ENABLED" in names


def test_status_and_http_handlers_no_secrets():
    body = handle_operations_status()
    assert body["ok"] is True
    assert "read_only_mode" in body
    assert "maintenance" in body
    blob = json.dumps(body).lower()
    assert "bearer " not in blob
    assert "api_key" not in blob
    assert "evidence_text" not in blob
    health = handle_operations_health()
    assert "components" in health
    dash = dashboard_snapshot()
    assert dash["ok"] is True


def test_alerts_informational_only():
    QUOTAS.set_hard_limit("benchmark_runs_per_day", 1, actor="admin")
    QUOTAS.consume("benchmark_runs_per_day")
    alerts = generate_alerts()
    assert any(a.code == "quota_exceeded" for a in alerts)
    assert all(a.informational_only for a in alerts)
    pub = alerts_public_dict()
    assert pub["informational_only"] is True


def test_usage_and_metrics():
    USAGE.set_active_users(3)
    USAGE.record_latency(120)
    USAGE.add_cost(0.01)
    OPERATIONS_METRICS.set_active(cases=2, workflows=1)
    OPERATIONS_METRICS.set_provider_utilization(0.25)
    snap = USAGE.to_public_dict()
    assert snap["active_users"] == 3
    assert snap["active_cases"] == 2
    assert snap["provider_utilization"] == 0.25
    prom = OPERATIONS_METRICS.render_prometheus()
    assert "active_cases 2" in prom
    assert "feature_flag_changes" in prom


def test_status_public_dict_writes_gate():
    st = status_public_dict()
    assert "writes_allowed" in st
    MAINTENANCE.enter(reject_new_workflows=True)
    assert writes_allowed() is False


def test_regression_imports_kc_stack():
    """Smoke: KC-021..030 surfaces still importable beside OCP."""
    from cobra_core.air import bridge as air_bridge
    from cobra_core.benchmark.runner import BenchmarkRunner
    from cobra_core.cial.config import load_cial_config
    from cobra_core.isf.registry import SKILL_REGISTRY
    from cobra_core.kef.config import load_kef_config
    from cobra_core.resilience.config import rrf_enabled

    assert load_cial_config() is not None
    assert air_bridge is not None
    assert len(SKILL_REGISTRY) >= 1
    assert load_kef_config() is not None
    assert isinstance(rrf_enabled(), bool)
    result = BenchmarkRunner().run_dataset("policy_review_v1")
    assert result.overall_score >= 0.0
    # OCP overall still computable
    assert overall_status() in set(ComponentHealth)
