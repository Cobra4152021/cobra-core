"""
KC-035 — Multi-Organization & Tenant Framework (MOTF).

Secure multi-organization investigation platform primitives.
Organizations never share data unless explicitly allowed.
"""

from cobra_core.organizations.config import OrganizationsConfig, load_organizations_config
from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
from cobra_core.organizations.routing import TENANT_ROUTER
from cobra_core.organizations.tenancy import TENANCY, TenantContext

__all__ = [
    "ORGANIZATION_REGISTRY",
    "OrganizationsConfig",
    "TENANCY",
    "TENANT_ROUTER",
    "TenantContext",
    "load_organizations_config",
]
