"""KC-036 Public API & SDK Framework tests."""

from __future__ import annotations

import json

import pytest

from cobra_core.api.audit import API_AUDIT
from cobra_core.api.errors import ApiErrorCode
from cobra_core.api.identity import sign_identity_assertion, verify_identity_assertion
from cobra_core.api.metrics import API_METRICS
from cobra_core.api.openapi import build_openapi_document, render_openapi_json
from cobra_core.api.pagination import decode_cursor, encode_cursor, paginate
from cobra_core.api.rate_limit import RateLimiter
from cobra_core.api.router import API_GATEWAY, ApiRequest, handle_public_api
from cobra_core.api.sdk.python.cobra_sdk.client import CobraClient, SDK_VERSION
from cobra_core.api.versioning import ApiVersionInfo, is_supported_version, parse_api_version
from cobra_core.api.webhooks import RESERVED_EVENTS
from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
from cobra_core.organizations.schemas import MembershipRole, ResourceKind
from cobra_core.organizations.tenancy import TENANCY
from cobra_core.security.identity import IDENTITY
from cobra_core.security.schemas import BuiltInRole


def _reset() -> None:
    API_GATEWAY.reset_for_tests()
    TENANCY.reset_for_tests()
    IDENTITY.reset_for_tests()
    from cobra_core.security.roles import ROLE_REGISTRY
    from cobra_core.security.authorization import AUTHORIZATION
    from cobra_core.security.audit import SECURITY_AUDIT
    from cobra_core.security.metrics import SECURITY_METRICS

    ROLE_REGISTRY.reset_for_tests()
    AUTHORIZATION.reset_for_tests()
    SECURITY_AUDIT.clear()
    SECURITY_METRICS.clear()


@pytest.fixture(autouse=True)
def _fixture():
    _reset()
    yield
    _reset()


def _auth_req(
    method: str,
    path: str,
    *,
    query: str = "",
    body: dict | None = None,
    principal_id: str = "sys_cobra",
    organization_id: str = "_system",
    authenticated: bool = True,
    identity_verified: bool = True,
) -> ApiRequest:
    return ApiRequest(
        method=method,
        path=path,
        query=query,
        headers={"X-Cobra-Sdk-Version": f"python/{SDK_VERSION}"},
        body=body,
        request_id="req_test",
        authenticated=authenticated,
        identity_verified=identity_verified,
        principal_id=principal_id,
        organization_id=organization_id,
        api_client_id=principal_id or "client_test",
    )


def test_versioning():
    assert parse_api_version("/api/v1/health") == "v1"
    assert is_supported_version("v1")
    assert not is_supported_version("v9")
    info = ApiVersionInfo().public_dict()
    assert info["current"] == "v1"
    assert "Breaking changes" in info["deprecation_policy"]


def test_openapi_deterministic():
    a = build_openapi_document()
    b = build_openapi_document()
    assert a == b
    assert a["openapi"] == "3.1.0"
    assert "/api/v1/organizations" in a["paths"]
    text1 = render_openapi_json()
    text2 = render_openapi_json()
    assert text1 == text2
    resp = API_GATEWAY.dispatch(_auth_req("GET", "/api/v1/openapi.json"))
    assert resp.status == 200
    assert resp.body["openapi"] == "3.1.0"


def test_pagination():
    items = [{"i": i} for i in range(10)]
    page = paginate(items, limit=3, cursor=None)
    assert len(page.items) == 3
    assert page.next_cursor
    page2 = paginate(items, limit=3, cursor=page.next_cursor)
    assert page2.items[0]["i"] == 3
    assert decode_cursor(encode_cursor(5)) == 5


def test_rate_limits():
    rl = RateLimiter(org_limit=2, client_limit=2, window_seconds=60)
    rl.check(organization_id="o1", api_client_id="c1")
    rl.check(organization_id="o1", api_client_id="c1")
    with pytest.raises(Exception) as exc:
        rl.check(organization_id="o1", api_client_id="c1")
    assert exc.value.error_code == ApiErrorCode.RATE_LIMITED  # type: ignore[attr-defined]


def test_authentication_required():
    resp = API_GATEWAY.dispatch(
        _auth_req("GET", "/api/v1/status", authenticated=False)
    )
    assert resp.status == 401
    assert resp.body["error_code"] == "unauthenticated"


def test_health_public():
    resp = API_GATEWAY.dispatch(
        _auth_req("GET", "/api/v1/health", authenticated=False)
    )
    assert resp.status == 200
    assert resp.body["ok"] is True


def test_unverified_identity_is_rejected():
    resp = API_GATEWAY.dispatch(
        _auth_req("GET", "/api/v1/status", identity_verified=False)
    )
    assert resp.status == 401
    assert resp.body["error_code"] == "unauthenticated"


def test_identity_assertion_rejects_spoofing_and_replay():
    secret = "test-secret"
    ts = 1_700_000_000
    signature = sign_identity_assertion(
        secret=secret,
        timestamp=ts,
        principal_id="user_a",
        organization_id="org_a",
        method="GET",
        path="/api/v1/cases",
    )
    headers = {
        "X-Cobra-Principal-Id": "user_a",
        "X-Cobra-Org-Id": "org_a",
        "X-Cobra-Identity-Timestamp": str(ts),
        "X-Cobra-Identity-Signature": signature,
    }
    verified = verify_identity_assertion(
        headers=headers,
        secret=secret,
        method="GET",
        path="/api/v1/cases",
        now=ts,
    )
    assert verified is not None
    assert verified.principal_id == "user_a"

    spoofed = dict(headers)
    spoofed["X-Cobra-Principal-Id"] = "sys_cobra"
    assert verify_identity_assertion(
        headers=spoofed,
        secret=secret,
        method="GET",
        path="/api/v1/cases",
        now=ts,
    ) is None
    assert verify_identity_assertion(
        headers=headers,
        secret=secret,
        method="POST",
        path="/api/v1/cases",
        now=ts,
    ) is None
    assert verify_identity_assertion(
        headers=headers,
        secret=secret,
        method="GET",
        path="/api/v1/cases",
        now=ts + 301,
    ) is None


def test_resource_groups_and_examples_flow():
    IDENTITY.bootstrap()
    owner = IDENTITY.create_user(
        display_name="API Owner",
        roles=[BuiltInRole.ADMINISTRATOR.value],
        principal_id="user_api_owner",
    )
    ORGANIZATION_REGISTRY.create_organization(
        name="API Org",
        owner=owner.principal_id,
        organization_id="org_api",
    )
    inv = IDENTITY.create_user(
        display_name="Inv",
        roles=[BuiltInRole.OBSERVER.value],
        principal_id="user_api_inv",
    )
    ORGANIZATION_REGISTRY.membership.add(
        principal_id=inv.principal_id,
        organization_id="org_api",
        roles=[MembershipRole.INVESTIGATOR],
    )

    # List organizations
    resp = API_GATEWAY.dispatch(
        _auth_req(
            "GET",
            "/api/v1/organizations",
            query="limit=10",
            principal_id=owner.principal_id,
            organization_id="org_api",
        )
    )
    assert resp.status == 200
    assert any(o["organization_id"] == "org_api" for o in resp.body["data"])

    # Create case
    resp = API_GATEWAY.dispatch(
        _auth_req(
            "POST",
            "/api/v1/cases",
            body={"organization_id": "org_api", "case_id": "case_api_1"},
            principal_id=inv.principal_id,
            organization_id="org_api",
        )
    )
    assert resp.status == 200
    assert resp.body["case"]["resource_id"] == "case_api_1"

    # Run workflow
    resp = API_GATEWAY.dispatch(
        _auth_req(
            "POST",
            "/api/v1/workflows/default/run",
            body={"organization_id": "org_api"},
            principal_id=inv.principal_id,
            organization_id="org_api",
        )
    )
    assert resp.status == 200
    assert resp.body["run"]["status"] == "accepted"

    # Evidence retrieve (tag then get)
    ORGANIZATION_REGISTRY.tag_resource(
        organization_id="org_api",
        resource_kind=ResourceKind.EVIDENCE_REF,
        resource_id="ev_api_1",
        resource_owner=inv.principal_id,
    )
    resp = API_GATEWAY.dispatch(
        _auth_req(
            "GET",
            "/api/v1/evidence/ev_api_1",
            principal_id=inv.principal_id,
            organization_id="org_api",
        )
    )
    assert resp.status == 200

    # Report (sample plugin)
    from cobra_core.plugins.manager import PLUGIN_MANAGER

    PLUGIN_MANAGER.reset_for_tests()
    PLUGIN_MANAGER.bootstrap_samples()
    resp = API_GATEWAY.dispatch(
        _auth_req("GET", "/api/v1/reports/policy_compliance_summary", principal_id=inv.principal_id, organization_id="org_api")
    )
    assert resp.status == 200

    # Plugins / benchmark / ops / security
    assert API_GATEWAY.dispatch(_auth_req("GET", "/api/v1/plugins", principal_id=inv.principal_id, organization_id="org_api")).status == 200
    assert API_GATEWAY.dispatch(_auth_req("GET", "/api/v1/benchmark/datasets", principal_id=inv.principal_id, organization_id="org_api")).status == 200
    assert API_GATEWAY.dispatch(_auth_req("GET", "/api/v1/operations/status", principal_id=inv.principal_id, organization_id="org_api")).status == 200
    assert API_GATEWAY.dispatch(_auth_req("GET", "/api/v1/security/status", principal_id=inv.principal_id, organization_id="org_api")).status == 200


def test_sdk_generation_surface():
    # Reference SDK importable; models/helpers present
    assert SDK_VERSION
    client = CobraClient("http://example.invalid", token="t")
    assert "Bearer t" in client._headers()["Authorization"]
    assert "python/" in client._headers()["X-Cobra-Sdk-Version"]
    # TypeScript SDK file exists
    from pathlib import Path

    ts = Path(__file__).resolve().parents[1] / "src/cobra_core/api/sdk/typescript/src/client.ts"
    assert ts.is_file()
    text = ts.read_text(encoding="utf-8")
    assert "export class CobraClient" in text


def test_audit_and_metrics():
    API_GATEWAY.dispatch(_auth_req("GET", "/api/v1/status"))
    snap = API_METRICS.snapshot()
    assert snap["api_requests"] >= 1
    assert "python/0.1.0" in snap["sdk_versions"] or snap["sdk_versions"]
    assert API_AUDIT.recent(limit=5)


def test_webhooks_reserved():
    st = API_GATEWAY.dispatch(_auth_req("GET", "/api/v1/status"))
    assert st.body["webhooks"]["delivery"] is False
    assert "case.created" in RESERVED_EVENTS


def test_unsupported_version():
    resp = API_GATEWAY.dispatch(_auth_req("GET", "/api/v9/health", authenticated=False))
    assert resp.status == 400
    assert resp.body["error_code"] == "version_unsupported"


def test_handle_public_api_helper():
    resp = handle_public_api(
        method="GET",
        path="/api/v1/health",
        authenticated=False,
        request_id="r1",
    )
    assert resp.status == 200


def test_regression_kc_021_through_035():
    from cobra_core.air import bridge as air_bridge
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
    assert API_GATEWAY.dispatch(_auth_req("GET", "/api/v1/status")).status == 200
