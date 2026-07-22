"""Load and validate immutable baseline lock records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class BaselineLockError(Exception):
    """Raised when baseline lock validation or immutability checks fail."""


class BaselineLockRecord(BaseModel):
    """Immutable reference to a frozen CobraBench baseline run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    lock_id: Annotated[str, Field(min_length=1)]
    run_id: Annotated[str, Field(min_length=1)]
    model_slug: Annotated[str, Field(min_length=1)]
    model_revision: Annotated[str, Field(min_length=1)]
    benchmark_version: Annotated[str, Field(min_length=1)]
    artifact_inventory_ref: Annotated[str, Field(min_length=1)]
    benchmark_release_hash: Annotated[str, Field(min_length=1)]
    protocol_path: Annotated[str, Field(min_length=1)]
    protocol_hash: Annotated[str, Field(min_length=1)]
    result_run_path: Annotated[str, Field(min_length=1)]
    result_inventory_hash: Annotated[str, Field(min_length=1)]
    scoring_implementation_version: Annotated[str, Field(min_length=1)]
    human_review_version: Annotated[str, Field(min_length=1)]
    report_references: list[str] = Field(default_factory=list)
    created_at: datetime
    immutable: bool = True
    notes: str | None = None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _sha256_directory_json_inventory(root: Path, *, pattern: str = "**/*") -> str:
    """Hash relative paths and file contents for a run directory inventory."""
    if not root.is_dir():
        msg = f"Run directory not found: {root}"
        raise BaselineLockError(msg)
    entries: list[str] = []
    for path in sorted(root.glob(pattern)):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            entries.append(f"{rel}:{_sha256_file(path)}")
    payload = "\n".join(entries)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_baseline_lock(path: Path | str) -> BaselineLockRecord:
    """Load and parse a baseline lock JSON file."""
    lock_path = Path(path)
    if not lock_path.is_file():
        msg = f"Baseline lock file not found: {lock_path}"
        raise BaselineLockError(msg)
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    return BaselineLockRecord.model_validate(data)


def validate_baseline_lock(
    record: BaselineLockRecord,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    """
    Validate that a baseline lock record matches on-disk artifacts.

    Returns a list of error messages; empty means valid.
    """
    root = repo_root or Path(__file__).resolve().parents[3]
    errors: list[str] = []

    run_path = Path(record.result_run_path)
    if not run_path.is_absolute():
        run_path = root / run_path
    if not run_path.is_dir():
        errors.append(f"Locked run directory missing: {run_path}")
    else:
        run_json = run_path / "run.json"
        if run_json.is_file():
            run_data = json.loads(run_json.read_text(encoding="utf-8"))
            if run_data.get("run_id") != record.run_id:
                errors.append(
                    f"run_id mismatch: lock={record.run_id!r} run.json={run_data.get('run_id')!r}"
                )
        else:
            errors.append(f"Locked run missing run.json: {run_json}")

        actual_hash = _sha256_directory_json_inventory(run_path)
        if actual_hash != record.result_inventory_hash:
            errors.append(
                "result_inventory_hash mismatch: "
                f"expected {record.result_inventory_hash}, got {actual_hash}"
            )

    protocol_path = Path(record.protocol_path)
    if not protocol_path.is_absolute():
        protocol_path = root / protocol_path
    if protocol_path.is_file():
        actual_protocol_hash = _sha256_file(protocol_path)
        if actual_protocol_hash != record.protocol_hash:
            errors.append(
                f"protocol_hash mismatch: expected {record.protocol_hash}, got {actual_protocol_hash}"
            )
    else:
        errors.append(f"Protocol file missing: {protocol_path}")

    if not record.immutable:
        errors.append("Baseline lock must have immutable=true")

    return errors


def _resolve_locked_run(
    lock_path: Path | str,
    *,
    repo_root: Path | None = None,
) -> tuple[BaselineLockRecord, Path]:
    record = load_baseline_lock(lock_path)
    root = repo_root or Path(__file__).resolve().parents[3]
    locked_run = Path(record.result_run_path)
    if not locked_run.is_absolute():
        locked_run = root / locked_run
    return record, locked_run.resolve()


def assert_baseline_not_overwritten(
    lock_path: Path | str,
    run_dir: Path | str,
    *,
    repo_root: Path | None = None,
) -> None:
    """
    Refuse to proceed if ``run_dir`` is the locked baseline and would be overwritten.

    Raises ``BaselineLockError`` when the target run directory matches the locked
    baseline path and the lock record marks it immutable.
    """
    record, locked_resolved = _resolve_locked_run(lock_path, repo_root=repo_root)
    if not record.immutable:
        return

    target_run = Path(run_dir).resolve()
    if target_run == locked_resolved:
        msg = (
            f"Refusing to overwrite locked baseline run {record.run_id} at {target_run}. "
            "Use a new run ID for diagnostic runs."
        )
        raise BaselineLockError(msg)


def assert_path_outside_locked_baseline(
    lock_path: Path | str,
    output_path: Path | str,
    *,
    repo_root: Path | None = None,
) -> None:
    """
    Refuse to write analysis artifacts into an immutable locked baseline run tree.

    Raises ``BaselineLockError`` when ``output_path`` is the locked run directory
    or any path nested under it.
    """
    record, locked_resolved = _resolve_locked_run(lock_path, repo_root=repo_root)
    if not record.immutable:
        return

    target = Path(output_path).resolve()
    if target == locked_resolved or locked_resolved in target.parents:
        msg = (
            f"Refusing to write analysis artifact into locked baseline run "
            f"{record.run_id} at {locked_resolved}. "
            "Write Phase 2E artifacts under evaluations/analysis/ or reports/ instead."
        )
        raise BaselineLockError(msg)


def compute_run_inventory_hash(run_dir: Path | str) -> str:
    """Compute inventory hash for a result run directory."""
    return _sha256_directory_json_inventory(Path(run_dir))
