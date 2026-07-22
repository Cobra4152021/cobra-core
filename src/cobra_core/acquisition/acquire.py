"""Pinned Hugging Face acquisition for approved manifests."""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from cobra_core.acquisition.hashing import format_sha256
from cobra_core.acquisition.inventory import (
    build_inventory,
    write_inventory_files,
)
from cobra_core.acquisition.quarantine import quarantine_acquisition
from cobra_core.acquisition.revisions import assert_pinned_revision
from cobra_core.schemas.manifest import (
    AcquisitionStatus,
    ArtifactFile,
    HashVerificationState,
    ModelManifest,
)
from cobra_core.storage.paths import (
    assert_outside_repo,
    resolve_model_paths,
)
from cobra_core.util.redact import redact_secrets

_HF_REPO = re.compile(r"^/?([^/]+)/([^/]+)/?$")


class AcquisitionError(RuntimeError):
    """Raised when acquisition cannot complete safely."""


def parse_hf_repo_id(source_repository: str) -> str:
    """Extract ``org/name`` from a Hugging Face URL or bare repo id."""
    text = str(source_repository).strip()
    if re.fullmatch(r"[^/\s]+/[^/\s]+", text):
        return text
    parsed = urlparse(text)
    if "huggingface.co" not in parsed.netloc.lower():
        raise AcquisitionError(
            f"source_repository is not a Hugging Face URL/id: {source_repository}"
        )
    match = _HF_REPO.match(parsed.path)
    if not match:
        raise AcquisitionError(f"cannot parse Hugging Face repo from {source_repository}")
    return f"{match.group(1)}/{match.group(2)}"


def estimate_storage_gate(
    *,
    available_free_bytes: int,
    expected_model_bytes: int = 20 * 1024**3,
    temporary_overhead_bytes: int = 8 * 1024**3,
    safety_margin_bytes: int = 20 * 1024**3,
) -> dict[str, Any]:
    required = expected_model_bytes + temporary_overhead_bytes + safety_margin_bytes
    passed = available_free_bytes >= required
    return {
        "expected_model_bytes": expected_model_bytes,
        "temporary_overhead_bytes": temporary_overhead_bytes,
        "safety_margin_bytes": safety_margin_bytes,
        "required_free_bytes": required,
        "available_free_bytes": available_free_bytes,
        "passed": passed,
        "message": (
            "storage gate passed"
            if passed
            else (
                f"insufficient free disk: need {required} bytes "
                f"(~{required / 1e9:.1f} GB), have {available_free_bytes}"
            )
        ),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redact_secrets(payload), indent=2) + "\n",
        encoding="utf-8",
    )


def update_manifest_from_inventory(
    manifest: ModelManifest,
    inventory_items: list[Any],
    *,
    local_artifact_root: str,
    local_inventory_ref: str,
) -> ModelManifest:
    """Return an acquired manifest with verified local hashes."""
    by_path = {item.relative_path: item for item in inventory_items}
    artifacts: list[ArtifactFile] = []
    for expected in manifest.artifact_files:
        item = by_path.get(expected.path)
        if item is None or item.sha256 is None:
            raise AcquisitionError(f"missing hashed artifact for {expected.path}")
        artifacts.append(
            ArtifactFile(
                path=expected.path,
                sha256=format_sha256(item.sha256),
                verification_state=HashVerificationState.VERIFIED,
                size_bytes=item.size_bytes,
            )
        )
    # Include unexpected but present files as verified extras for completeness.
    expected_paths = {item.path for item in manifest.artifact_files}
    for rel, item in sorted(by_path.items()):
        if rel in expected_paths or item.sha256 is None:
            continue
        artifacts.append(
            ArtifactFile(
                path=rel,
                sha256=format_sha256(item.sha256),
                verification_state=HashVerificationState.VERIFIED,
                size_bytes=item.size_bytes,
            )
        )

    return manifest.model_copy(
        update={
            "artifact_files": artifacts,
            "acquisition_status": AcquisitionStatus.VERIFIED,
            "acquisition_date": date.today(),
            "local_artifact_root": local_artifact_root,
            "local_inventory_ref": local_inventory_ref,
            "notes": (
                (manifest.notes or "") + " | Phase 2B: verified and locally SHA256-verified. "
                "Development baseline only; not Cobra Core."
            ).strip(" |"),
        }
    )


def acquire_from_manifest(
    manifest_path: Path,
    *,
    repo_root: Path,
    model_home: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Download a pinned Hugging Face revision for an approved manifest.

    Requires ``huggingface_hub``. Does not print tokens.
    """
    manifest = ModelManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    revision = assert_pinned_revision(manifest.model_revision)
    if revision != assert_pinned_revision(manifest.source_commit):
        raise AcquisitionError("model_revision and source_commit must match for acquisition")

    repo_id = parse_hf_repo_id(str(manifest.source_repository))
    paths = resolve_model_paths(
        manifest.provider,
        manifest.model_name,
        revision,
        model_home=model_home,
    )
    assert_outside_repo(paths.root, repo_root)
    paths.ensure_layout()

    log_path = paths.provenance / "acquisition-log.json"
    report_path = paths.provenance / "acquisition-report.md"
    state_path = paths.download_state / "state.json"

    if dry_run:
        payload = {
            "dry_run": True,
            "repo_id": repo_id,
            "revision": revision,
            "artifact_dir": str(paths.artifacts),
        }
        _write_json(state_path, payload)
        return payload

    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise AcquisitionError(
            "huggingface_hub is required for acquisition; "
            "install with: pip install 'cobra-core[acquisition]'"
        ) from exc

    started = datetime.now(UTC)
    _write_json(
        state_path,
        {
            "status": "downloading",
            "repo_id": repo_id,
            "revision": revision,
            "started_at": started.isoformat(),
        },
    )

    try:
        snapshot_download(
            repo_id=repo_id,
            revision=revision,
            local_dir=str(paths.artifacts),
        )
    except Exception as exc:
        quarantine_acquisition(
            paths,
            reason="download_failed",
            details={"error": str(exc), "repo_id": repo_id, "revision": revision},
        )
        _write_json(
            log_path,
            {
                "status": "failed",
                "error": str(exc),
                "repo_id": repo_id,
                "revision": revision,
            },
        )
        raise AcquisitionError(f"download failed; quarantined: {exc}") from exc

    expected = [item.path for item in manifest.artifact_files]
    inventory = build_inventory(
        paths.artifacts,
        model_name=manifest.model_name,
        revision=revision,
        expected_paths=expected,
        compute_hashes=True,
    )
    inv_path = paths.provenance / "artifact-inventory.json"
    sums_path = paths.hashes / "SHA256SUMS"
    write_inventory_files(inventory, inv_path, sums_path)

    if not inventory.complete:
        quarantine_acquisition(
            paths,
            reason="incomplete_download",
            details={"missing_expected": inventory.missing_expected},
        )
        raise AcquisitionError(
            "incomplete download; missing: " + ", ".join(inventory.missing_expected)
        )

    # License presence check
    license_names = {"license", "license.txt"}
    if not any(item.relative_path.lower() in license_names for item in inventory.items):
        quarantine_acquisition(paths, reason="license_missing", details={})
        raise AcquisitionError("LICENSE file missing after download")

    updated = update_manifest_from_inventory(
        manifest,
        inventory.items,
        local_artifact_root=str(paths.artifacts),
        local_inventory_ref=str(inv_path),
    )
    # Write updated manifest beside provenance and back to repo path if under model-cards
    acquired_manifest_path = paths.provenance / "ModelManifest.acquired.json"
    acquired_manifest_path.write_text(
        updated.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    manifest_path.write_text(updated.model_dump_json(indent=2) + "\n", encoding="utf-8")

    finished = datetime.now(UTC)
    total_bytes = sum(item.size_bytes for item in inventory.items)
    log_payload = {
        "status": "verified",
        "repo_id": repo_id,
        "revision": revision,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "artifact_count": len(inventory.items),
        "total_bytes": total_bytes,
        "inventory": str(inv_path),
        "sha256sums": str(sums_path),
        "manifest": str(manifest_path),
    }
    _write_json(log_path, log_payload)
    _write_json(state_path, {"status": "complete", **log_payload})
    report_path.write_text(
        "\n".join(
            [
                f"# Acquisition report — {manifest.model_name}",
                "",
                f"- Repo: `{repo_id}`",
                f"- Revision: `{revision}`",
                f"- Artifacts: {len(inventory.items)}",
                f"- Total bytes: {total_bytes}",
                f"- Inventory: `{inv_path}`",
                f"- SHA256SUMS: `{sums_path}`",
                "- Status: verified / locally verified",
                "",
                "Tokens and auth headers are never written to this report.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return log_payload
