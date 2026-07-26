"""KEF access control — permission checks before evidence is returned."""

from __future__ import annotations

from dataclasses import dataclass

from cobra_core.kef.types import EvidenceItem, EvidencePermissions


@dataclass(frozen=True)
class Principal:
    """Actor requesting evidence (no secrets)."""

    org_id: str = ""
    role: str = "investigator"
    classification_ceiling: str = "confidential"
    user_id: str = ""  # never used as metric label


def check_access(item: EvidenceItem, principal: Principal) -> bool:
    perms = item.permissions or EvidencePermissions()
    return perms.allows(
        role=principal.role,
        classification_ceiling=principal.classification_ceiling,
    )


def filter_permitted(
    items: list[EvidenceItem], principal: Principal
) -> tuple[list[EvidenceItem], list[EvidenceItem]]:
    """Return (allowed, denied)."""
    allowed: list[EvidenceItem] = []
    denied: list[EvidenceItem] = []
    for item in items:
        if check_access(item, principal):
            allowed.append(item)
        else:
            denied.append(item)
    return allowed, denied
