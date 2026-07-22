#!/usr/bin/env python3
"""Regenerate INVENTORY.json for a frozen CobraBench release."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.benchmarks.release import release_dir  # noqa: E402


def sha256_bytes(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def build_inventory(release_root: Path) -> dict[str, object]:
    cases_dir = release_root / "cases"
    entries: list[dict[str, str]] = []
    for path in sorted(cases_dir.glob("*.json")):
        content = path.read_bytes()
        entries.append(
            {
                "filename": path.name,
                "sha256": sha256_bytes(content),
            }
        )
    metadata_path = release_root / "metadata.json"
    release_version = "0.1"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        release_version = str(metadata.get("release_version", release_version))
    return {
        "release_version": release_version,
        "case_count": len(entries),
        "cases": entries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build CobraBench release INVENTORY.json")
    parser.add_argument(
        "--version",
        default="0.1",
        help="Release version slug (default: 0.1)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (default: release root / INVENTORY.json)",
    )
    args = parser.parse_args(argv)

    release_root = release_dir(args.version)
    output = args.output or (release_root / "INVENTORY.json")
    inventory = build_inventory(release_root)
    output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output} ({inventory['case_count']} case(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
