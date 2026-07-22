#!/usr/bin/env python3
"""Re-hash local artifacts and compare to an acquired manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.acquisition.hashing import format_sha256, sha256_file  # noqa: E402
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = ModelManifest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
    if not manifest.local_artifact_root:
        print("ERROR: manifest has no local_artifact_root", file=sys.stderr)
        return 2
    root = Path(manifest.local_artifact_root)
    mismatches = 0
    for artifact in manifest.artifact_files:
        path = root / artifact.path
        if not path.is_file():
            print(f"MISSING {artifact.path}")
            mismatches += 1
            continue
        digest = format_sha256(sha256_file(path))
        if artifact.sha256 and digest != artifact.sha256:
            print(f"MISMATCH {artifact.path}")
            mismatches += 1
        else:
            print(f"OK {artifact.path}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
