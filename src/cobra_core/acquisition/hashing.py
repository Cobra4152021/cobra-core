"""Streaming SHA256 helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path, *, chunk_size: int = CHUNK_SIZE) -> str:
    """Compute SHA256 of a file using streaming reads."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_sha256sums(
    entries: list[tuple[str, str]],
    output: Path,
) -> Path:
    """
    Write GNU-style SHA256SUMS.

    ``entries`` must already be in deterministic order: (relative_path, sha256).
    """
    lines = [f"{digest}  {rel_path}" for rel_path, digest in entries]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return output


def format_sha256(digest: str) -> str:
    """Normalize and validate a hex SHA256 digest."""
    cleaned = digest.strip().lower()
    if len(cleaned) != 64 or any(c not in "0123456789abcdef" for c in cleaned):
        raise ValueError(f"invalid sha256 digest: {digest!r}")
    return cleaned
