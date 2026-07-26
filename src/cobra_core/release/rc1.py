"""RC1 certification orchestrator — feature freeze evidence pack."""

from __future__ import annotations

import time
from typing import Any

from cobra_core.release.freeze import freeze_manifest
from cobra_core.release.soak import run_timed_soak, staging_24h_status

RC1_VERSION = "v1.0.0-rc1"


def _api_compatibility() -> dict[str, Any]:
    from cobra_core.api.openapi import build_openapi_document
    from cobra_core.api.pagination import paginate
    from cobra_core.api.rate_limit import RateLimiter
    from cobra_core.api.router import API_GATEWAY, ApiRequest
    from cobra_core.api.sdk.python.cobra_sdk.client import CobraClient, SDK_VERSION
    from cobra_core.api.versioning import ApiVersionInfo, is_supported_version
    from cobra_core.production.integrity import openapi_checksum

    doc = build_openapi_document()
    doc2 = build_openapi_document()
    page = paginate([{"i": i} for i in range(5)], limit=2)
    unauth = API_GATEWAY.dispatch(
        ApiRequest(method="GET", path="/api/v1/status", authenticated=False, request_id="rc1")
    )
    auth = API_GATEWAY.dispatch(
        ApiRequest(method="GET", path="/api/v1/status", authenticated=True, request_id="rc1a")
    )
    rl = RateLimiter(org_limit=1, client_limit=1, window_seconds=60)
    rl.check(organization_id="o", api_client_id="c")
    limited = False
    try:
        rl.check(organization_id="o", api_client_id="c")
    except Exception:  # noqa: BLE001
        limited = True
    client = CobraClient("http://example.invalid", token="t")
    return {
        "ok": (
            doc == doc2
            and doc["openapi"] == "3.1.0"
            and is_supported_version("v1")
            and page.next_cursor is not None
            and unauth.status == 401
            and auth.status == 200
            and limited
            and "Bearer t" in client._headers()["Authorization"]
            and bool(openapi_checksum())
            and ApiVersionInfo().current == "v1"
            and bool(SDK_VERSION)
        ),
        "openapi_checksum": openapi_checksum(),
        "sdk_version": SDK_VERSION,
        "versioning": ApiVersionInfo().public_dict(),
        "auth_unauthenticated_status": unauth.status,
        "auth_authenticated_status": auth.status,
        "rate_limit_enforced": limited,
        "pagination_next_cursor": page.next_cursor is not None,
    }


def _plugin_compatibility() -> dict[str, Any]:
    from cobra_core.plugins.manager import PLUGIN_MANAGER
    from cobra_core.plugins.schemas import PluginState

    PLUGIN_MANAGER.reset_for_tests()
    enabled = PLUGIN_MANAGER.bootstrap_samples()
    required = {
        "sample.vehicle_skill",
        "sample.policy_report",
        "sample.budget_dataset",
        "sample.case_template",
    }
    have = set(enabled)
    lifecycle_ok = True
    details: dict[str, Any] = {}
    for pid in sorted(required):
        try:
            PLUGIN_MANAGER.disable(pid)
            PLUGIN_MANAGER.enable(pid)
            PLUGIN_MANAGER.reload(pid)
            st = PLUGIN_MANAGER.get(pid)["state"]
            details[pid] = st
            if st != PluginState.ENABLED.value:
                lifecycle_ok = False
        except Exception as exc:  # noqa: BLE001
            lifecycle_ok = False
            details[pid] = type(exc).__name__
    return {
        "ok": required.issubset(have) and lifecycle_ok,
        "loaded": sorted(have),
        "required": sorted(required),
        "lifecycle": details,
    }


def _security_review() -> dict[str, Any]:
    from cobra_core.organizations.config import load_organizations_config
    from cobra_core.production.security_review import run_security_review
    from cobra_core.security import authorize
    from cobra_core.security.identity import IDENTITY
    from cobra_core.security.schemas import BuiltInRole, DecisionEffect, ResourceType
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
    from cobra_core.organizations.schemas import MembershipRole
    from cobra_core.organizations.tenancy import TENANCY
    from cobra_core.security.roles import ROLE_REGISTRY

    TENANCY.reset_for_tests()
    ROLE_REGISTRY.reset_for_tests()
    IDENTITY.reset_for_tests()
    IDENTITY.bootstrap()
    a = IDENTITY.create_user(
        display_name="A", roles=[BuiltInRole.INVESTIGATOR.value], principal_id="rc1_user_a"
    )
    b = IDENTITY.create_user(
        display_name="B", roles=[BuiltInRole.INVESTIGATOR.value], principal_id="rc1_user_b"
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="A", owner=a.principal_id, organization_id="org_rc1_a", seed_departments=False
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="B", owner=b.principal_id, organization_id="org_rc1_b", seed_departments=False
    )
    ORGANIZATION_REGISTRY.membership.add(
        principal_id=a.principal_id,
        organization_id="org_rc1_a",
        roles=[MembershipRole.INVESTIGATOR],
    )
    cross = authorize(
        principal_id=b.principal_id,
        action="retrieve_evidence",
        resource_type=ResourceType.EVIDENCE,
        attributes={"organization_id": "org_rc1_a"},
        organization_id="org_rc1_b",
    )
    sec = run_security_review()
    motf = load_organizations_config()
    return {
        "ok": sec["ok"] and cross.effect == DecisionEffect.DENY and motf.allow_cross_org is False,
        "security_review": sec,
        "cross_org_denied": cross.effect == DecisionEffect.DENY,
        "allow_cross_org": motf.allow_cross_org,
    }


def _recovery() -> dict[str, Any]:
    from pathlib import Path
    import tempfile

    from cobra_core.production.backup import BACKUP
    from cobra_core.production.migrations import MIGRATIONS
    from cobra_core.production.restore import RESTORE
    from cobra_core.production.startup import run_startup_validation

    MIGRATIONS.reset_for_tests()
    with tempfile.TemporaryDirectory() as td:
        BACKUP.reset_for_tests(root=Path(td))
        env = {
            "COBRA_CORE_AUTH_SECRET": "rc1-cert-secret-value-32chars!!!!",
            "PRHF_ABORT_ON_CRITICAL": "true",
        }
        startup = run_startup_validation(env=env, correlation_id="rc1_recovery")
        dry = MIGRATIONS.dry_run()
        applied = MIGRATIONS.apply("m001_motf_registry")
        rolled = MIGRATIONS.rollback("m001_motf_registry")
        art = BACKUP.create(actor="rc1")
        restore_dry = RESTORE.restore_file(art.path, dry_run=True)
        restore = RESTORE.restore_file(art.path, dry_run=False)
    return {
        "ok": (
            startup.ok
            and dry["ok"]
            and applied.get("ok")
            and rolled.get("ok")
            and restore_dry.get("ok")
            and restore.get("applied")
        ),
        "startup_ok": startup.ok,
        "migration_dry_run": dry["ok"],
        "migration_apply_rollback": bool(applied.get("ok") and rolled.get("ok")),
        "backup_restore": bool(restore.get("applied")),
    }


def _performance() -> dict[str, Any]:
    from cobra_core.production.loadtest import run_load_test
    from cobra_core.production.startup import run_startup_validation

    env = {"COBRA_CORE_AUTH_SECRET": "rc1-cert-secret-value-32chars!!!!"}
    startup = run_startup_validation(env=env, correlation_id="rc1_perf")
    sizes = {}
    for n in (100, 500, 1000, 5000):
        sizes[str(n)] = run_load_test(n)
    return {
        "ok": all(v["ok"] for v in sizes.values()) and startup.ok,
        "startup_duration_s": startup.duration_s,
        "sizes": {
            k: {
                "ok": v["ok"],
                "errors": v["errors"],
                "latency_ms": v["latency_ms"],
                "elapsed_s": v["elapsed_s"],
            }
            for k, v in sizes.items()
        },
    }


def _benchmark_smoke() -> dict[str, Any]:
    from cobra_core.benchmark.runner import BenchmarkRunner

    result = BenchmarkRunner().run_dataset("policy_review_v1")
    return {
        "ok": result.overall_score >= 0.0,
        "dataset": "policy_review_v1",
        "overall_score": result.overall_score,
    }


def run_rc1_certification(*, local_soak_s: float = 30.0) -> dict[str, Any]:
    """
    Execute RC1 certification pack (offline/local).

    Does not claim 24h staging soak completion.
    """
    t0 = time.perf_counter()
    phases: dict[str, Any] = {}
    phases["freeze"] = {"ok": True, "manifest": freeze_manifest()}
    phases["api_compatibility"] = _api_compatibility()
    phases["plugin_compatibility"] = _plugin_compatibility()
    phases["security"] = _security_review()
    phases["recovery"] = _recovery()
    phases["performance"] = _performance()
    phases["benchmark"] = _benchmark_smoke()
    phases["local_soak"] = run_timed_soak(duration_s=local_soak_s, interval_s=0.05, label="rc1")
    phases["staging_soak_24h"] = staging_24h_status()

    blocking = []
    if not phases["staging_soak_24h"]["complete"]:
        blocking.append("phase_7_soak_24h_incomplete")
    for key in (
        "api_compatibility",
        "plugin_compatibility",
        "security",
        "recovery",
        "performance",
        "benchmark",
        "local_soak",
    ):
        if not phases[key].get("ok"):
            blocking.append(f"{key}_failed")

    # Offline pack can be green while staging soak blocks RC approval.
    offline_ok = not any(b.endswith("_failed") for b in blocking)
    approved = offline_ok and not blocking
    return {
        "version": RC1_VERSION,
        "feature_freeze": True,
        "production_enabled": False,
        "offline_certification_ok": offline_ok,
        "release_candidate_approved": approved,
        "blocking_issues": blocking,
        "phases": phases,
        "elapsed_s": round(time.perf_counter() - t0, 4),
        "verdict": (
            "PASS — Release Candidate Approved"
            if approved
            else (
                "PARTIAL — RC blocked by listed issues"
                if offline_ok
                else "FAIL — Release Candidate rejected"
            )
        ),
    }
