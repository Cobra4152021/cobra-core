#!/usr/bin/env python3
"""Validate ModelManifest JSON files."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.cli import validate_manifests_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(validate_manifests_main())
