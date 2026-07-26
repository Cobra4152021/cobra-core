"""KC-034 Identity, Security & Policy Framework tests."""

from __future__ import annotations

import pytest

from cobra_core.security.audit import SECURITY_AUDIT
from cobra_core.security.authorization import AUTHORIZATION, authorize
from cobra_core.security.config import load_security_config
from cobra_core.security.errors import SecurityError, SecurityErrorCode
from cobra_core.security.http_api import (
    handle_security_permissions,
    handle_security_policies,
    handle_security_roles,
    handle_security_sessions,
    handle_security_status,
)
from cobra_core.security.identity import IDENTITY
from cobra_core.security.metrics import SECURITY_METRICS
from cobra_core.security.permissions import PERMISSION_REGISTRY
from cobra_core.security.policy import POLICY_ENGINE
from cobra_core.security.roles import ROLE_REGISTRY
from cobra_core.security.schemas import (
    BuiltInRole,
    DecisionEffect,
    PrincipalType,
    ResourceRef,
    ResourceType,
)
from cobra_core.security.sessions import SESSION_STORE


def _reset_ispf() -> None:
    IDENTITY.reset_for_tests()
    ROLE_REGISTRY.reset_for_tests()
    PERMISSION_REGISTRY.reset_for_tests()
    POLICY_ENGINE.reset_for_tests()
    SESSION_STORE.reset_for_tests()
    SECURITY_METRICS.clear()
    SECURITY_AUDIT.clear()
    AUTHORIZATION.reset_for_tests()


@pytest.fixture(autouse=True)
def _ispf_fixture():
    _reset_ispf()
    yield
    _reset_ispf()


def test_identity_bootstrap_principals():
    ids = IDENTITY.bootstrap()
    assert "sys_cobra" in ids
    assert "svc_evidence_vault" in ids
    assert "svc_operations" in ids
    assert "svc_benchmark" in ids
    vault = IDENTITY.resolve("svc_evidence_vault")
    assert vault.principal_type == PrincipalType.SERVICE
    perms = IDENTITY.effective_permissions("svc_evidence_vault")
    assert "retrieve_evidence" in perms
    assert "manage_users" not in perms


def test_roles_and_permissions_additive():
    IDENTITY.bootstrap()
    user = IDENTITY.create_user(
        display_name="Inv",
        roles=[BuiltInRole.INVESTIGATOR.value, BuiltInRole.REVIEWER.value],
        principal_id="user_combo",
    )
    perms = IDENTITY.effective_permissions(user.principal_id)
    assert "run_workflow" in perms
    assert "approve_findings" in perms
    roles = handle_security_roles()["roles"]
    assert any(r["role"] == "administrator" for r in roles)
    perms_list = handle_security_permissions()["permissions"]
    assert any(p["permission"] == "create_case" for p in perms_list)


def test_no_admin_bypass_flag():
    cfg = load_security_config()
    assert cfg.admin_bypass is False
    status = handle_security_status()
    assert status["admin_bypass"] is False


def test_policy_investigator_run_workflow_allow():
    IDENTITY.bootstrap()
    inv = IDENTITY.create_user(
        display_name="Investigator",
        roles=[BuiltInRole.INVESTIGATOR.value],
        principal_id="user_inv",
    )
    d = authorize(
        principal_id=inv.principal_id,
        action="run_workflow",
        resource_type=ResourceType.WORKFLOW,
        resource_id="wf_1",
    )
    assert d.effect == DecisionEffect.ALLOW
    assert d.policy_id == "pol_investigator_allow_run_workflow"


def test_policy_reviewer_approve_findings_allow():
    IDENTITY.bootstrap()
    rev = IDENTITY.create_user(
        display_name="Reviewer",
        roles=[BuiltInRole.REVIEWER.value],
        principal_id="user_rev",
    )
    d = authorize(
        principal_id=rev.principal_id,
        action="approve_findings",
        resource_type=ResourceType.FINDING,
    )
    assert d.effect == DecisionEffect.ALLOW
    assert d.policy_id == "pol_reviewer_allow_approve_findings"


def test_policy_observer_retrieve_evidence_deny():
    IDENTITY.bootstrap()
    obs = IDENTITY.create_user(
        display_name="Observer",
        roles=[BuiltInRole.OBSERVER.value],
        principal_id="user_obs",
    )
    d = authorize(
        principal_id=obs.principal_id,
        action="retrieve_evidence",
        resource_type=ResourceType.EVIDENCE,
        resource_id="ev_1",
    )
    assert d.effect == DecisionEffect.DENY
    assert d.policy_id == "pol_observer_deny_retrieve_evidence"


def test_authorization_default_deny_unknown_action_permission():
    IDENTITY.bootstrap()
    obs = IDENTITY.create_user(
        display_name="Observer",
        roles=[BuiltInRole.OBSERVER.value],
        principal_id="user_obs2",
    )
    d = authorize(
        principal_id=obs.principal_id,
        action="manage_users",
        resource_type=ResourceType.SYSTEM,
    )
    assert d.effect == DecisionEffect.DENY
    assert d.policy_id in {"default_deny", "permission_required"}


def test_conditional_owner_close_case():
    IDENTITY.bootstrap()
    inv = IDENTITY.create_user(
        display_name="Investigator",
        roles=[BuiltInRole.INVESTIGATOR.value],
        principal_id="user_owner",
    )
    # Investigator lacks close_case in builtin role — should deny even if owner.
    d = authorize(
        principal_id=inv.principal_id,
        action="close_case",
        resource=ResourceRef(
            resource_type=ResourceType.CASE,
            resource_id="case_1",
            attributes={"owner": "user_owner"},
        ),
    )
    assert d.effect == DecisionEffect.DENY

    sup = IDENTITY.create_user(
        display_name="Supervisor",
        roles=[BuiltInRole.SUPERVISOR.value],
        principal_id="user_sup",
    )
    d2 = authorize(
        principal_id=sup.principal_id,
        action="close_case",
        resource=ResourceRef(
            resource_type=ResourceType.CASE,
            resource_id="case_1",
            attributes={"owner": "user_sup"},
        ),
    )
    assert d2.effect == DecisionEffect.ALLOW
    assert d2.policy_id == "pol_owner_conditional_close_case"

    d3 = authorize(
        principal_id=sup.principal_id,
        action="close_case",
        resource=ResourceRef(
            resource_type=ResourceType.CASE,
            resource_id="case_1",
            attributes={"owner": "someone_else"},
        ),
    )
    assert d3.effect == DecisionEffect.CONDITIONAL


def test_session_create_and_revoke():
    IDENTITY.bootstrap()
    user = IDENTITY.create_user(
        display_name="Sess",
        roles=[BuiltInRole.INVESTIGATOR.value],
        principal_id="user_sess",
    )
    perms = sorted(IDENTITY.effective_permissions(user.principal_id))
    session, token = SESSION_STORE.create(
        principal_id=user.principal_id,
        roles=user.roles,
        permissions=perms,
    )
    assert token
    assert "token" not in session.public_dict()
    resolved = SESSION_STORE.resolve_token(token)
    assert resolved.session_id == session.session_id
    SESSION_STORE.revoke(session.session_id)
    with pytest.raises(SecurityError) as exc:
        SESSION_STORE.resolve_token(token)
    assert exc.value.code == SecurityErrorCode.SESSION_REVOKED
    body = handle_security_sessions()
    assert body["ok"] is True
    assert all("token" not in s or s.get("token") is None for s in body["sessions"])
    assert all("token_fingerprint" in s for s in body["sessions"])


def test_audit_and_metrics():
    IDENTITY.bootstrap()
    inv = IDENTITY.create_user(
        display_name="Inv",
        roles=[BuiltInRole.INVESTIGATOR.value],
        principal_id="user_m",
    )
    authorize(
        principal_id=inv.principal_id,
        action="run_workflow",
        resource_type=ResourceType.WORKFLOW,
    )
    authorize(
        principal_id=inv.principal_id,
        action="manage_users",
        resource_type=ResourceType.SYSTEM,
    )
    snap = SECURITY_METRICS.snapshot()
    assert snap["authorization_requests"] >= 2
    assert snap["authorization_allowed"] >= 1
    assert snap["authorization_denied"] >= 1
    assert snap["policy_evaluations"] >= 1
    events = SECURITY_AUDIT.recent(limit=20)
    assert any(e["event"] == "authorization" for e in events)
    # No credentials in audit payloads
    blob = str(events)
    assert "password" not in blob.lower() or "[redacted]" in blob


def test_http_security_surfaces():
    st = handle_security_status()
    assert st["ok"] is True
    assert st["framework"] == "ispf"
    assert handle_security_policies()["policies"]
    assert handle_security_roles()["roles"]
    assert handle_security_permissions()["permissions"]


def test_custom_role():
    IDENTITY.bootstrap()
    ROLE_REGISTRY.register_custom("field_agent", ["run_workflow", "view_metrics"])
    user = IDENTITY.create_user(
        display_name="Agent",
        roles=["field_agent"],
        principal_id="user_agent",
    )
    d = authorize(
        principal_id=user.principal_id,
        action="run_workflow",
        resource_type=ResourceType.WORKFLOW,
    )
    assert d.effect == DecisionEffect.ALLOW


def test_regression_kc_021_through_033():
    """Smoke: prior King Cobra surfaces remain importable beside ISPF."""
    from cobra_core.air import bridge as air_bridge
    from cobra_core.benchmark.runner import BenchmarkRunner
    from cobra_core.cial.config import load_cial_config
    from cobra_core.isf.registry import SKILL_REGISTRY
    from cobra_core.kef.config import load_kef_config
    from cobra_core.operations.health import overall_status
    from cobra_core.operations.schemas import ComponentHealth
    from cobra_core.plugins.manager import PLUGIN_MANAGER
    from cobra_core.resilience.config import rrf_enabled

    assert load_cial_config() is not None
    assert air_bridge is not None
    assert len(SKILL_REGISTRY) >= 1
    assert load_kef_config() is not None
    assert isinstance(rrf_enabled(), bool)
    assert overall_status() in set(ComponentHealth)
    result = BenchmarkRunner().run_dataset("policy_review_v1")
    assert result.overall_score >= 0.0
    PLUGIN_MANAGER.reset_for_tests()
    PLUGIN_MANAGER.bootstrap_samples()
    assert len(PLUGIN_MANAGER.list_plugins()) >= 4
    IDENTITY.bootstrap()
    assert authorize(
        principal_id="sys_cobra",
        action="view_security",
        resource_type=ResourceType.SYSTEM,
    ).effect == DecisionEffect.ALLOW
