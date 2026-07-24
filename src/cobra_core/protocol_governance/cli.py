"""CLI for Cobra Protocol V1 governance conformance."""

from __future__ import annotations

import argparse
from pathlib import Path

from cobra_core.protocol_governance.verify import (
    default_protocol_root,
    repo_root_from_here,
    verify_protocol_package,
    write_manifest,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify Cobra Protocol V1 governance package (schemas/fixtures/hashes).",
    )
    parser.add_argument(
        "--protocol-root",
        type=Path,
        default=None,
        help="Path to protocol/v1 (default: <repo>/protocol/v1)",
    )
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Regenerate protocol/v1/MANIFEST.json from current schemas/fixtures",
    )
    args = parser.parse_args(argv)

    repo_root = repo_root_from_here()
    protocol_root = args.protocol_root or default_protocol_root(repo_root)

    if args.write_manifest:
        path = write_manifest(protocol_root, repo_root=repo_root)
        print(f"wrote {path}")
        # Fall through to verify after write.

    errors = verify_protocol_package(protocol_root, repo_root=repo_root)
    if errors:
        print("FAIL cobra-protocol-conformance")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("PASS cobra-protocol-conformance")
    print(f"  protocol_root={protocol_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
