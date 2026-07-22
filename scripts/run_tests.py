#!/usr/bin/env python3
"""Run unit tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    return subprocess.call([sys.executable, "-m", "pytest"], cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
