"""Backup framework — metadata/config/audit/org/case indexes; Vault refs only."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cobra_core.production.audit import PRODUCTION_AUDIT
from cobra_core.production.metrics import PRODUCTION_METRICS


@dataclass(frozen=True)
class BackupArtifact:
    backup_id: str
    created_at: float
    path: str
    kinds: tuple[str, ...]
    vault_references_only: bool = True

    def public_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "created_at": self.created_at,
            "path": self.path,
            "kinds": list(self.kinds),
            "vault_references_only": self.vault_references_only,
        }


def _collect_payload() -> dict[str, Any]:
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
    from cobra_core.organizations.schemas import ResourceKind
    from cobra_core.production.configuration import load_production_config
    from cobra_core.production.integrity import integrity_report
    from cobra_core.security.audit import SECURITY_AUDIT

    orgs = [o.public_dict() for o in ORGANIZATION_REGISTRY.list_organizations()]
    case_index = []
    evidence_refs = []
    for org in ORGANIZATION_REGISTRY.list_organizations():
        for r in ORGANIZATION_REGISTRY.resources_for_org(org.organization_id):
            if r.resource_kind == ResourceKind.CASE:
                case_index.append(r.public_dict())
            elif r.resource_kind == ResourceKind.EVIDENCE_REF:
                # Reference only — do not embed vault object bytes
                evidence_refs.append(
                    {
                        "resource_id": r.resource_id,
                        "organization_id": r.organization_id,
                        "vault_object": False,
                        "reference_only": True,
                    }
                )
    return {
        "format": "prhf_backup_v1",
        "created_at": time.time(),
        "configuration": {
            "production": load_production_config().__dict__,
            # Never include secrets
            "notes": "secrets excluded",
        },
        "organizations": orgs,
        "case_metadata_index": case_index,
        "evidence_references": evidence_refs,
        "audit": SECURITY_AUDIT.recent(limit=100),
        "integrity": integrity_report(),
        "vault_objects_included": False,
    }


class BackupService:
    def __init__(self, *, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else Path.cwd() / ".prhf_backups"
        self._last: BackupArtifact | None = None

    def reset_for_tests(self, *, root: str | Path | None = None) -> None:
        if root is not None:
            self.root = Path(root)
        self._last = None

    def create(self, *, actor: str = "admin") -> BackupArtifact:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            backup_id = f"bak_{uuid.uuid4().hex[:12]}"
            path = self.root / f"{backup_id}.json"
            payload = _collect_payload()
            payload["backup_id"] = backup_id
            path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
            art = BackupArtifact(
                backup_id=backup_id,
                created_at=time.time(),
                path=str(path),
                kinds=(
                    "configuration",
                    "organizations",
                    "case_metadata",
                    "evidence_references",
                    "audit",
                    "integrity",
                ),
                vault_references_only=True,
            )
            self._last = art
            PRODUCTION_METRICS.incr("backup_success")
            PRODUCTION_AUDIT.record(
                "backup",
                actor=actor,
                result="success",
                backup_id=backup_id,
                vault_objects_included=False,
            )
            return art
        except Exception as exc:  # noqa: BLE001
            PRODUCTION_METRICS.incr("backup_failure")
            PRODUCTION_AUDIT.record(
                "backup", actor=actor, result="failure", error=type(exc).__name__
            )
            raise


BACKUP = BackupService()
