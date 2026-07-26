"""Authenticated ISPF HTTP handlers — no credential exposure."""

from __future__ import annotations

from typing import Any

from cobra_core.security.audit import SECURITY_AUDIT
from cobra_core.security.authorization import AUTHORIZATION
from cobra_core.security.config import load_security_config
from cobra_core.security.identity import IDENTITY
from cobra_core.security.metrics import SECURITY_METRICS
from cobra_core.security.permissions import PERMISSION_REGISTRY
from cobra_core.security.policy import POLICY_ENGINE
from cobra_core.security.roles import ROLE_REGISTRY
from cobra_core.security.sessions import SESSION_STORE


def handle_security_status() -> dict[str, Any]:
    IDENTITY.ensure_bootstrapped()
    cfg = load_security_config()
    return {
        "ok": True,
        "framework": "ispf",
        "enabled": cfg.enabled,
        "default_deny": cfg.default_deny,
        "admin_bypass": False,
        "session_ttl_seconds": cfg.session_ttl_seconds,
        "principals": len(IDENTITY.principals.list_public()),
        "metrics": SECURITY_METRICS.snapshot(),
        "audit_channel": "identity_security_policy",
    }


def handle_security_roles() -> dict[str, Any]:
    IDENTITY.ensure_bootstrapped()
    return {"ok": True, "roles": ROLE_REGISTRY.list_roles()}


def handle_security_permissions() -> dict[str, Any]:
    return {"ok": True, "permissions": PERMISSION_REGISTRY.public_list()}


def handle_security_policies() -> dict[str, Any]:
    return {"ok": True, "policies": POLICY_ENGINE.list_policies()}


def handle_security_sessions() -> dict[str, Any]:
    # Public session metadata only — no raw tokens.
    return {"ok": True, "sessions": SESSION_STORE.list_public()}


def handle_security_metrics() -> dict[str, Any]:
    return {"ok": True, "metrics": SECURITY_METRICS.snapshot()}


def handle_security_audit(*, limit: int = 50) -> dict[str, Any]:
    return {"ok": True, "entries": SECURITY_AUDIT.recent(limit=limit)}


def handle_security_authorize(
    *,
    principal_id: str,
    action: str,
    resource_type: str,
    resource_id: str = "*",
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optional internal helper (not required by KC-034 HTTP list)."""
    decision = AUTHORIZATION.authorize(
        principal_id=principal_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        attributes=attributes,
    )
    return {"ok": True, "decision": decision.public_dict()}
