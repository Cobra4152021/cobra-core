"""Canonical content hashing for Protocol V1 governance artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


def hash_files(root: Path, files: list[Path]) -> str:
    """SHA-256 over sorted relative paths + file bytes (NUL-delimited records)."""
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def list_schema_files(protocol_root: Path) -> list[Path]:
    return sorted((protocol_root / "schemas").glob("*.schema.json"))


def list_fixture_files(protocol_root: Path) -> list[Path]:
    return sorted((protocol_root / "fixtures").glob("*.json"))
