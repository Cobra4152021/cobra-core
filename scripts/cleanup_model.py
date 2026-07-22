#!/usr/bin/env python3
"""Safe cleanup helpers for quarantined acquisitions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.acquisition.quarantine import safe_cleanup_quarantine  # noqa: E402
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402
from cobra_core.storage.paths import resolve_model_paths  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    manifest = ModelManifest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
    paths = resolve_model_paths(
        manifest.provider,
        manifest.model_name,
        manifest.model_revision,
    )
    safe_cleanup_quarantine(paths, confirm=args.confirm)
    print(f"Cleaned quarantine under {paths.quarantine}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
