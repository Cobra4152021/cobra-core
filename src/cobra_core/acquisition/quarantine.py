"""Quarantine workflow for failed acquisitions."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from cobra_core.storage.paths import ModelStoragePaths


class QuarantineError(RuntimeError):
    """Raised when an acquisition is quarantined and must not be used."""


class QuarantinedModelError(RuntimeError):
    """Raised when inference attempts to load a quarantined model."""


def quarantine_marker_path(paths: ModelStoragePaths) -> Path:
    return paths.root / "QUARANTINED.json"


def is_quarantined(paths: ModelStoragePaths) -> bool:
    return quarantine_marker_path(paths).is_file()


def assert_not_quarantined(paths: ModelStoragePaths) -> None:
    if is_quarantined(paths):
        raise QuarantinedModelError(
            f"model at {paths.root} is quarantined and cannot be used for inference"
        )


def quarantine_acquisition(
    paths: ModelStoragePaths,
    *,
    reason: str,
    details: dict[str, object] | None = None,
) -> Path:
    """
    Flag an acquisition as quarantined and preserve diagnostics.

    Moves ``artifacts`` into ``quarantine/<timestamp>/`` when present,
    writes a marker file, and leaves hash/provenance diagnostics in place.
    """
    paths.ensure_layout()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = paths.quarantine / stamp
    target.mkdir(parents=True, exist_ok=True)

    moved_artifacts = False
    if paths.artifacts.exists() and any(paths.artifacts.iterdir()):
        dest = target / "artifacts"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(paths.artifacts), str(dest))
        paths.artifacts.mkdir(parents=True, exist_ok=True)
        moved_artifacts = True

    payload = {
        "quarantined_at": datetime.now(UTC).isoformat(),
        "reason": reason,
        "details": details or {},
        "moved_artifacts": moved_artifacts,
        "quarantine_dir": str(target),
    }
    marker = quarantine_marker_path(paths)
    marker.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (target / "quarantine-reason.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return marker


def safe_cleanup_quarantine(paths: ModelStoragePaths, *, confirm: bool = False) -> None:
    """Remove quarantine trees only when explicitly confirmed."""
    if not confirm:
        raise QuarantineError("refusing cleanup without confirm=True")
    if paths.quarantine.exists():
        shutil.rmtree(paths.quarantine)
        paths.quarantine.mkdir(parents=True, exist_ok=True)
    marker = quarantine_marker_path(paths)
    if marker.exists():
        marker.unlink()
