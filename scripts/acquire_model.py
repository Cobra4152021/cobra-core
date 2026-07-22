#!/usr/bin/env python3
"""Acquire a pinned model from an approved manifest (weights outside git)."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.acquisition.acquire import (  # noqa: E402
    AcquisitionError,
    acquire_from_manifest,
    estimate_storage_gate,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-home", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--expected-gb",
        type=float,
        default=20.0,
        help="Expected model size in GB for storage gate",
    )
    args = parser.parse_args(argv)

    free = shutil.disk_usage(args.model_home or "D:\\").free
    gate = estimate_storage_gate(
        available_free_bytes=free,
        expected_model_bytes=int(args.expected_gb * 1024**3),
    )
    print(gate["message"])
    if not gate["passed"]:
        print("STOP: storage gate failed; no download started.", file=sys.stderr)
        return 2

    try:
        result = acquire_from_manifest(
            args.manifest,
            repo_root=ROOT,
            model_home=args.model_home,
            dry_run=args.dry_run,
        )
    except AcquisitionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json_dumps(result))
    return 0


def json_dumps(payload: object) -> str:
    import json

    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
