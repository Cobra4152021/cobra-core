"""Migration framework only — dry-run, pending/applied, rollback, compatibility."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cobra_core.production.audit import PRODUCTION_AUDIT
from cobra_core.production.metrics import PRODUCTION_METRICS


@dataclass(frozen=True)
class Migration:
    migration_id: str
    description: str
    version: str
    compatible_from: str = "0.9.0"
    compatible_to: str = "0.9.99"


# Built-in framework migrations (no destructive schema ops in KC-037).
BUILTIN_MIGRATIONS: tuple[Migration, ...] = (
    Migration("m001_motf_registry", "Initialize organization registry metadata", "1"),
    Migration("m002_ispf_audit_fields", "Ensure ISPF audit tenant fields", "1"),
    Migration("m003_pasf_openapi", "Record OpenAPI checksum baseline", "1"),
)


@dataclass
class MigrationState:
    applied: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)


class MigrationFramework:
    def __init__(self, *, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else None
        self._lock = threading.Lock()
        self._state = MigrationState()
        self._migrations = list(BUILTIN_MIGRATIONS)

    def reset_for_tests(self) -> None:
        with self._lock:
            self._state = MigrationState()

    def list_all(self) -> list[dict[str, Any]]:
        return [
            {
                "migration_id": m.migration_id,
                "description": m.description,
                "version": m.version,
                "compatible_from": m.compatible_from,
                "compatible_to": m.compatible_to,
            }
            for m in self._migrations
        ]

    def pending(self) -> list[Migration]:
        with self._lock:
            applied = set(self._state.applied)
        return [m for m in self._migrations if m.migration_id not in applied]

    def applied(self) -> list[str]:
        with self._lock:
            return list(self._state.applied)

    def compatibility_ok(self, core_version: str = "0.9.0rc1") -> bool:
        # Simple major.minor gate for framework migrations.
        base = ".".join(core_version.lstrip("v").split(".")[:2])
        return base.startswith("0.9")

    def dry_run(self) -> dict[str, Any]:
        pending = self.pending()
        ok = self.compatibility_ok()
        report = {
            "ok": ok,
            "dry_run": True,
            "pending": [m.migration_id for m in pending],
            "applied": self.applied(),
            "compatible": ok,
        }
        PRODUCTION_AUDIT.record("migration_dry_run", pending=report["pending"], compatible=ok)
        return report

    def apply(self, migration_id: str, *, dry_run: bool = False) -> dict[str, Any]:
        if dry_run:
            return self.dry_run()
        if not self.compatibility_ok():
            PRODUCTION_METRICS.incr("migration_failure")
            PRODUCTION_AUDIT.record("migration", result="incompatible", migration_id=migration_id)
            return {"ok": False, "error": "compatibility_check_failed"}
        matches = [m for m in self._migrations if m.migration_id == migration_id]
        if not matches:
            PRODUCTION_METRICS.incr("migration_failure")
            return {"ok": False, "error": "not_found"}
        with self._lock:
            if migration_id in self._state.applied:
                return {"ok": True, "already_applied": True, "migration_id": migration_id}
            self._state.applied.append(migration_id)
            self._state.history.append(
                {"migration_id": migration_id, "ts": time.time(), "action": "apply"}
            )
            if self.root:
                self.root.mkdir(parents=True, exist_ok=True)
                (self.root / "applied.json").write_text(
                    json.dumps(self._state.applied, indent=2), encoding="utf-8"
                )
        PRODUCTION_METRICS.incr("migration_success")
        PRODUCTION_AUDIT.record("migration", result="applied", migration_id=migration_id)
        return {"ok": True, "migration_id": migration_id, "applied": True}

    def rollback(self, migration_id: str, *, dry_run: bool = False) -> dict[str, Any]:
        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "would_rollback": migration_id,
                "currently_applied": migration_id in self.applied(),
            }
        with self._lock:
            if migration_id not in self._state.applied:
                PRODUCTION_METRICS.incr("migration_failure")
                return {"ok": False, "error": "not_applied"}
            self._state.applied = [m for m in self._state.applied if m != migration_id]
            self._state.history.append(
                {"migration_id": migration_id, "ts": time.time(), "action": "rollback"}
            )
        PRODUCTION_METRICS.incr("migration_success")
        PRODUCTION_AUDIT.record("migration", result="rolled_back", migration_id=migration_id)
        return {"ok": True, "migration_id": migration_id, "rolled_back": True}


MIGRATIONS = MigrationFramework()
