"""Restore framework — validate compatibility before applying metadata restore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cobra_core.production.audit import PRODUCTION_AUDIT
from cobra_core.production.metrics import PRODUCTION_METRICS


class RestoreError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def validate_backup_compatibility(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("format") != "prhf_backup_v1":
        errors.append("unsupported backup format")
    if payload.get("vault_objects_included") is True:
        errors.append("backup must not include vault object bodies")
    if "organizations" not in payload:
        errors.append("missing organizations")
    if "integrity" not in payload:
        errors.append("missing integrity block")
    return errors


class RestoreService:
    def restore_file(
        self,
        path: str | Path,
        *,
        actor: str = "admin",
        dry_run: bool = False,
        apply_organizations: bool = True,
    ) -> dict[str, Any]:
        p = Path(path)
        if not p.is_file():
            PRODUCTION_METRICS.incr("restore_failure")
            raise RestoreError("not_found", f"backup not found: {path}")
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            PRODUCTION_METRICS.incr("restore_failure")
            raise RestoreError("invalid_json", str(exc)) from exc

        errors = validate_backup_compatibility(payload)
        if errors:
            PRODUCTION_METRICS.incr("restore_failure")
            PRODUCTION_AUDIT.record("restore", actor=actor, result="incompatible", errors=errors)
            raise RestoreError("incompatible", "; ".join(errors))

        report: dict[str, Any] = {
            "ok": True,
            "dry_run": dry_run,
            "backup_id": payload.get("backup_id"),
            "organizations": len(payload.get("organizations") or []),
            "case_metadata_index": len(payload.get("case_metadata_index") or []),
            "evidence_references": len(payload.get("evidence_references") or []),
            "audit_entries": len(payload.get("audit") or []),
            "applied": False,
        }
        if dry_run:
            PRODUCTION_AUDIT.record("restore", actor=actor, result="dry_run", **report)
            return report

        if apply_organizations:
            from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
            from cobra_core.organizations.validation import OrganizationValidationError

            # Restore org metadata into registry when missing (non-destructive merge).
            for org in payload.get("organizations") or []:
                oid = str(org.get("organization_id") or "")
                if not oid:
                    continue
                try:
                    ORGANIZATION_REGISTRY.get(oid)
                except OrganizationValidationError:
                    ORGANIZATION_REGISTRY.create_organization(
                        name=str(org.get("name") or oid),
                        owner=str(org.get("owner") or "sys_cobra"),
                        organization_id=oid,
                        seed_departments=False,
                    )

        report["applied"] = True
        PRODUCTION_METRICS.incr("restore_success")
        PRODUCTION_AUDIT.record("restore", actor=actor, result="success", **report)
        return report


RESTORE = RestoreService()
