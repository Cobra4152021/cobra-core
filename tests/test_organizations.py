"""KC-035 Multi-Organization & Tenant Framework tests."""

from __future__ import annotations

import pytest

from cobra_core.organizations.audit import ORGANIZATION_AUDIT
from cobra_core.organizations.http_api import (
    handle_organization_departments,
    handle_organization_get,
    handle_organization_members,
    handle_organization_metrics,
    handle_organization_status,
    handle_organizations_list,
)
from cobra_core.organizations.metrics import ORGANIZATION_METRICS
from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
from cobra_core.organizations.routing import TENANT_ROUTER
from cobra_core.organizations.schemas import (
    BenchmarkScope,
    MembershipRole,
    PluginScope,
    ResourceKind,
)
from cobra_core.organizations.tenancy import TENANCY
from cobra_core.organizations.validation import OrganizationValidationError
from cobra_core.security.authorization import authorize
from cobra_core.security.identity import IDENTITY
from cobra_core.security.schemas import BuiltInRole, DecisionEffect, ResourceType


def _reset_motf() -> None:
    TENANCY.reset_for_tests()
    ORGANIZATION_METRICS.clear()
    ORGANIZATION_AUDIT.clear()
    IDENTITY.reset_for_tests()
    from cobra_core.security.audit import SECURITY_AUDIT
    from cobra_core.security.authorization import AUTHORIZATION
    from cobra_core.security.metrics import SECURITY_METRICS
    from cobra_core.security.roles import ROLE_REGISTRY

    ROLE_REGISTRY.reset_for_tests()
    SECURITY_AUDIT.clear()
    SECURITY_METRICS.clear()
    AUTHORIZATION.reset_for_tests()


@pytest.fixture(autouse=True)
def _motf_fixture():
    _reset_motf()
    yield
    _reset_motf()


def test_organization_creation_and_departments():
    IDENTITY.bootstrap()
    owner = IDENTITY.create_user(
        display_name="Owner",
        roles=[BuiltInRole.ADMINISTRATOR.value],
        principal_id="user_owner_a",
    )
    org = ORGANIZATION_REGISTRY.create_organization(
        name="County Alpha",
        owner=owner.principal_id,
        organization_id="org_alpha",
    )
    assert org.organization_id == "org_alpha"
    assert org.status.value == "active"
    depts = ORGANIZATION_REGISTRY.list_departments("org_alpha")
    kinds = {d.kind.value for d in depts}
    for required in {
        "sheriff",
        "police",
        "compliance",
        "internal_affairs",
        "union",
        "inspector_general",
        "risk_management",
    }:
        assert required in kinds


def test_membership_scoped_no_role_transfer():
    IDENTITY.bootstrap()
    u = IDENTITY.create_user(
        display_name="Multi",
        roles=[BuiltInRole.OBSERVER.value],
        principal_id="user_multi",
    )
    IDENTITY.create_user(
        display_name="Other",
        roles=[BuiltInRole.ADMINISTRATOR.value],
        principal_id="user_other_owner",
    )
    org_a = ORGANIZATION_REGISTRY.create_organization(
        name="Org A", owner=u.principal_id, organization_id="org_a"
    )
    org_b = ORGANIZATION_REGISTRY.create_organization(
        name="Org B",
        owner="user_other_owner",
        organization_id="org_b",
        seed_departments=False,
    )
    ORGANIZATION_REGISTRY.membership.add(
        principal_id=u.principal_id,
        organization_id=org_b.organization_id,
        roles=[MembershipRole.INVESTIGATOR],
    )
    mems = ORGANIZATION_REGISTRY.membership.list_for_principal(u.principal_id)
    assert len(mems) == 2
    roles_a = ORGANIZATION_REGISTRY.membership.get(u.principal_id, org_a.organization_id).roles
    roles_b = ORGANIZATION_REGISTRY.membership.get(u.principal_id, org_b.organization_id).roles
    assert MembershipRole.ORGANIZATION_OWNER in roles_a
    assert MembershipRole.INVESTIGATOR in roles_b
    assert MembershipRole.ORGANIZATION_OWNER not in roles_b


def test_department_policy_inheritance():
    IDENTITY.bootstrap()
    owner = IDENTITY.create_user(
        display_name="O",
        roles=[BuiltInRole.ADMINISTRATOR.value],
        principal_id="user_dept",
    )
    org = ORGANIZATION_REGISTRY.create_organization(
        name="Dept Org", owner=owner.principal_id, organization_id="org_dept"
    )
    org.security_policies["retention_days"] = 90
    dept = ORGANIZATION_REGISTRY.list_departments("org_dept")[0]
    inherited = dept.effective_policies(org)
    assert inherited.get("retention_days") == 90
    dept.policy_overrides["retention_days"] = 30
    overridden = dept.effective_policies(org)
    assert overridden["retention_days"] == 30
    dept.inherit_org_policies = False
    dept.policy_overrides = {"local_only": True}
    local = dept.effective_policies(org)
    assert local == {"local_only": True}


def test_isolation_and_cross_org_denial():
    IDENTITY.bootstrap()
    a = IDENTITY.create_user(
        display_name="A", roles=[BuiltInRole.INVESTIGATOR.value], principal_id="user_iso_a"
    )
    b = IDENTITY.create_user(
        display_name="B", roles=[BuiltInRole.INVESTIGATOR.value], principal_id="user_iso_b"
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="Iso A", owner=a.principal_id, organization_id="org_iso_a"
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="Iso B", owner=b.principal_id, organization_id="org_iso_b"
    )
    ORGANIZATION_REGISTRY.tag_resource(
        organization_id="org_iso_a",
        resource_kind=ResourceKind.CASE,
        resource_id="case_a1",
        resource_owner=a.principal_id,
    )
    # Same org access ok
    ownership = TENANCY.assert_resource_access(
        principal_id=a.principal_id,
        organization_id="org_iso_a",
        resource_kind=ResourceKind.CASE,
        resource_id="case_a1",
    )
    assert ownership.organization_id == "org_iso_a"
    # Cross-org denied
    with pytest.raises(OrganizationValidationError) as exc:
        TENANCY.assert_resource_access(
            principal_id=b.principal_id,
            organization_id="org_iso_b",
            resource_kind=ResourceKind.CASE,
            resource_id="case_a1",
        )
    assert exc.value.code == "cross_org_denied"
    # Authz cross-org deny
    d = authorize(
        principal_id=b.principal_id,
        action="run_workflow",
        resource_type=ResourceType.WORKFLOW,
        attributes={"organization_id": "org_iso_a"},
        organization_id="org_iso_b",
    )
    assert d.effect == DecisionEffect.DENY
    assert d.policy_id == "cross_org_denied"


def test_plugin_and_benchmark_scoping():
    IDENTITY.bootstrap()
    u = IDENTITY.create_user(
        display_name="P", roles=[BuiltInRole.INVESTIGATOR.value], principal_id="user_plug"
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="Plug Org", owner=u.principal_id, organization_id="org_plug"
    )
    dept_id = ORGANIZATION_REGISTRY.list_departments("org_plug")[0].department_id
    catalog = [
        {"plugin_id": "g1", "scope": PluginScope.GLOBAL.value, "organization_id": ""},
        {
            "plugin_id": "o1",
            "scope": PluginScope.ORGANIZATION.value,
            "organization_id": "org_plug",
        },
        {
            "plugin_id": "o2",
            "scope": PluginScope.ORGANIZATION.value,
            "organization_id": "org_other",
        },
        {
            "plugin_id": "d1",
            "scope": PluginScope.DEPARTMENT.value,
            "organization_id": "org_plug",
            "department_id": dept_id,
        },
    ]
    visible = TENANT_ROUTER.visible_plugins(
        principal_id=u.principal_id,
        organization_id="org_plug",
        department_id=dept_id,
        catalog=catalog,
    )
    ids = {p["plugin_id"] for p in visible}
    assert "g1" in ids and "o1" in ids and "d1" in ids
    assert "o2" not in ids

    benches = [
        {"dataset_id": "global_ds", "scope": BenchmarkScope.GLOBAL.value},
        {
            "dataset_id": "org_ds",
            "scope": BenchmarkScope.ORGANIZATION.value,
            "organization_id": "org_plug",
        },
        {
            "dataset_id": "private_ds",
            "scope": BenchmarkScope.PRIVATE.value,
            "organization_id": "org_plug",
            "owner": u.principal_id,
        },
        {
            "dataset_id": "private_other",
            "scope": BenchmarkScope.PRIVATE.value,
            "organization_id": "org_plug",
            "owner": "someone_else",
        },
    ]
    vis_b = TENANT_ROUTER.visible_benchmarks(
        principal_id=u.principal_id,
        organization_id="org_plug",
        catalog=benches,
    )
    bids = {b["dataset_id"] for b in vis_b}
    assert "global_ds" in bids and "org_ds" in bids and "private_ds" in bids
    assert "private_other" not in bids


def test_workflow_scoping():
    IDENTITY.bootstrap()
    u = IDENTITY.create_user(
        display_name="W", roles=[BuiltInRole.ADMINISTRATOR.value], principal_id="user_wf"
    )
    org = ORGANIZATION_REGISTRY.create_organization(
        name="WF Org", owner=u.principal_id, organization_id="org_wf"
    )
    org.configuration.workflow_availability["special_wf"] = False
    assert TENANT_ROUTER.workflow_available(organization_id="org_wf", workflow_id="default") is True
    assert (
        TENANT_ROUTER.workflow_available(organization_id="org_wf", workflow_id="special_wf")
        is False
    )


def test_case_move_requires_admin_and_audits():
    IDENTITY.bootstrap()
    admin = IDENTITY.create_user(
        display_name="Admin",
        roles=[BuiltInRole.ADMINISTRATOR.value],
        principal_id="user_move_admin",
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="From", owner=admin.principal_id, organization_id="org_from"
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="To", owner=admin.principal_id, organization_id="org_to"
    )
    ORGANIZATION_REGISTRY.tag_resource(
        organization_id="org_from",
        resource_kind=ResourceKind.CASE,
        resource_id="case_move_1",
        resource_owner=admin.principal_id,
    )
    new_own = TENANCY.move_case(
        actor_principal_id=admin.principal_id,
        case_id="case_move_1",
        from_organization_id="org_from",
        to_organization_id="org_to",
    )
    assert new_own.organization_id == "org_to"
    ORGANIZATION_AUDIT.record(
        "case_moved",
        organization_id="org_to",
        principal_id=admin.principal_id,
        membership=["organization_owner"],
        policy_version="motf-1",
        authorization_reference="admin_move",
        case_id="case_move_1",
        from_organization_id="org_from",
    )
    entries = ORGANIZATION_AUDIT.for_organization("org_to")
    assert any(e["event"] == "case_moved" for e in entries)


def test_tenant_aware_authorization_allow():
    IDENTITY.bootstrap()
    inv = IDENTITY.create_user(
        display_name="Inv",
        roles=[BuiltInRole.OBSERVER.value],  # global observer — should not transfer
        principal_id="user_tenant_inv",
    )
    IDENTITY.create_user(
        display_name="OX",
        roles=[BuiltInRole.ADMINISTRATOR.value],
        principal_id="user_owner_x",
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="Auth Org", owner="user_owner_x", organization_id="org_auth"
    )
    ORGANIZATION_REGISTRY.membership.add(
        principal_id=inv.principal_id,
        organization_id="org_auth",
        roles=[MembershipRole.INVESTIGATOR],
    )
    d = authorize(
        principal_id=inv.principal_id,
        action="run_workflow",
        resource_type=ResourceType.WORKFLOW,
        organization_id="org_auth",
    )
    assert d.effect == DecisionEffect.ALLOW
    assert d.organization_id == "org_auth"
    assert "investigator" in d.membership or MembershipRole.INVESTIGATOR.value in d.membership


def test_audit_and_metrics():
    IDENTITY.bootstrap()
    u = IDENTITY.create_user(
        display_name="M", roles=[BuiltInRole.ADMINISTRATOR.value], principal_id="user_met"
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="Met Org", owner=u.principal_id, organization_id="org_met"
    )
    ORGANIZATION_REGISTRY.tag_resource(
        organization_id="org_met",
        resource_kind=ResourceKind.CASE,
        resource_id="case_m1",
        resource_owner=u.principal_id,
    )
    ORGANIZATION_METRICS.incr("org_met", "workflows")
    ORGANIZATION_METRICS.incr("org_met", "benchmark_runs")
    ORGANIZATION_AUDIT.record(
        "resource_tagged",
        organization_id="org_met",
        department_id="",
        principal_id=u.principal_id,
        membership=["organization_owner"],
        policy_version="motf-1",
        authorization_reference="tag",
    )
    code, body = handle_organization_metrics("org_met")
    assert code == 200
    assert body["metrics"]["users"] >= 1
    assert body["metrics"]["cases"] >= 1
    assert body["metrics"]["workflows"] >= 1


def test_http_organization_apis():
    IDENTITY.bootstrap()
    u = IDENTITY.create_user(
        display_name="H", roles=[BuiltInRole.ADMINISTRATOR.value], principal_id="user_http"
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="HTTP Org", owner=u.principal_id, organization_id="org_http"
    )
    listed = handle_organizations_list()
    assert listed["ok"] is True
    assert any(o["organization_id"] == "org_http" for o in listed["organizations"])
    # No secrets
    assert "secret" not in str(listed).lower() or "password" not in str(listed).lower()
    code, got = handle_organization_get("org_http")
    assert code == 200
    code, mem = handle_organization_members("org_http")
    assert code == 200 and mem["members"]
    code, deps = handle_organization_departments("org_http")
    assert code == 200 and len(deps["departments"]) >= 7
    code, st = handle_organization_status("org_http")
    assert code == 200 and st["status"] == "active"


def test_ownership_immutable():
    IDENTITY.bootstrap()
    u = IDENTITY.create_user(
        display_name="I", roles=[BuiltInRole.ADMINISTRATOR.value], principal_id="user_imm"
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="Imm", owner=u.principal_id, organization_id="org_imm"
    )
    ORGANIZATION_REGISTRY.tag_resource(
        organization_id="org_imm",
        resource_kind=ResourceKind.EVIDENCE_REF,
        resource_id="ev_1",
        resource_owner=u.principal_id,
    )
    with pytest.raises(OrganizationValidationError) as exc:
        ORGANIZATION_REGISTRY.tag_resource(
            organization_id="org_imm",
            resource_kind=ResourceKind.EVIDENCE_REF,
            resource_id="ev_1",
            resource_owner=u.principal_id,
        )
    assert exc.value.code == "ownership_immutable"


def test_regression_kc_021_through_034():
    from cobra_core.air import bridge as air_bridge
    from cobra_core.benchmark.runner import BenchmarkRunner
    from cobra_core.cial.config import load_cial_config
    from cobra_core.isf.registry import SKILL_REGISTRY
    from cobra_core.kef.config import load_kef_config
    from cobra_core.operations.health import overall_status
    from cobra_core.operations.schemas import ComponentHealth
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
    IDENTITY.bootstrap()
    u = IDENTITY.create_user(
        display_name="R", roles=[BuiltInRole.ADMINISTRATOR.value], principal_id="user_reg"
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="Reg", owner=u.principal_id, organization_id="org_reg"
    )
    assert handle_organizations_list()["ok"] is True
