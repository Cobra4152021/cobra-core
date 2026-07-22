#!/usr/bin/env python3
"""Produce an empty evaluation report template."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.cli import report_template_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(report_template_main())
