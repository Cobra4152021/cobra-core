"""Artifact inventory generation after download."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from cobra_core.acquisition.hashing import format_sha256, sha256_file, write_sha256sums


class ArtifactType(StrEnum):
    WEIGHT = "weight"
    CONFIG = "config"
    TOKENIZER = "tokenizer"
    LICENSE = "license"
    MODEL_CARD = "model_card"
    INDEX = "index"
    OTHER = "other"


class HashSource(StrEnum):
    LOCAL_CALCULATED = "local_calculated"
    UPSTREAM_PROVIDED = "upstream_provided"
    METADATA_ONLY = "metadata_only"
    NONE = "none"


class InventoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relative_path: str
    size_bytes: Annotated[int, Field(ge=0)]
    sha256: str | None = None
    artifact_type: ArtifactType
    verification_status: str
    hash_source: HashSource = HashSource.NONE


class ArtifactInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created_at: datetime
    model_name: str
    revision: str
    artifact_root: str
    items: list[InventoryItem]
    complete: bool
    missing_expected: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def classify_artifact(relative_path: str) -> ArtifactType:
    name = relative_path.replace("\\", "/").lower()
    if name.endswith(".safetensors") or name.endswith(".bin") or name.endswith(".gguf"):
        return ArtifactType.WEIGHT
    if name in {"license", "license.txt"} or name.endswith("/license"):
        return ArtifactType.LICENSE
    if name.endswith("readme.md") or name.endswith("modelcard.md"):
        return ArtifactType.MODEL_CARD
    if "tokenizer" in name or name in {"vocab.json", "merges.txt", "tokenizer.json"}:
        return ArtifactType.TOKENIZER
    if name.endswith(".index.json") or name.endswith("index.json"):
        return ArtifactType.INDEX
    if name.endswith(".json") or name.endswith(".txt"):
        return ArtifactType.CONFIG
    return ArtifactType.OTHER


def iter_files_sorted(root: Path) -> list[Path]:
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and ".cache" not in path.relative_to(root).parts
    ]
    return sorted(files, key=lambda p: p.relative_to(root).as_posix().lower())


def build_inventory(
    artifact_root: Path,
    *,
    model_name: str,
    revision: str,
    expected_paths: list[str] | None = None,
    compute_hashes: bool = True,
) -> ArtifactInventory:
    """Enumerate artifacts under ``artifact_root`` in deterministic order."""
    if not artifact_root.is_dir():
        raise FileNotFoundError(f"artifact root missing: {artifact_root}")

    items: list[InventoryItem] = []
    for path in iter_files_sorted(artifact_root):
        rel = path.relative_to(artifact_root).as_posix()
        digest: str | None = None
        hash_source = HashSource.NONE
        status = "present"
        if compute_hashes:
            digest = format_sha256(sha256_file(path))
            hash_source = HashSource.LOCAL_CALCULATED
            status = "hashed"
        items.append(
            InventoryItem(
                relative_path=rel,
                size_bytes=path.stat().st_size,
                sha256=digest,
                artifact_type=classify_artifact(rel),
                verification_status=status,
                hash_source=hash_source,
            )
        )

    present = {item.relative_path for item in items}
    missing = sorted(set(expected_paths or []) - present)
    return ArtifactInventory(
        created_at=datetime.now(UTC),
        model_name=model_name,
        revision=revision,
        artifact_root=str(artifact_root),
        items=items,
        complete=not missing,
        missing_expected=missing,
        notes=[]
        if not missing
        else ["One or more expected manifest artifacts are missing from disk."],
    )


def write_inventory_files(
    inventory: ArtifactInventory,
    provenance_path: Path,
    hashes_path: Path,
) -> tuple[Path, Path]:
    """Write artifact-inventory.json and SHA256SUMS."""
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(
        inventory.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    hashed = [
        (item.relative_path, item.sha256) for item in inventory.items if item.sha256 is not None
    ]
    write_sha256sums(hashed, hashes_path)
    return provenance_path, hashes_path
