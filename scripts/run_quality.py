#!/usr/bin/env python3
"""Run lint, format check, typecheck, tests, and validators."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "run_lint.py",
    "run_format_check.py",
    "run_typecheck.py",
    "run_tests.py",
    "validate_cases.py",
    "validate_manifests.py",
]


def main() -> int:
    for name in SCRIPTS:
        print(f"==> {name}")
        code = subprocess.call([sys.executable, str(ROOT / "scripts" / name)], cwd=ROOT)
        if code != 0:
            print(f"FAILED: {name}", file=sys.stderr)
            return code
    print("OK: all quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
