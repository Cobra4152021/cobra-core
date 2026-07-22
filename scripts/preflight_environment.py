#!/usr/bin/env python3
"""Collect local hardware/runtime inventory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.environment.probe import collect_runtime_environment  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evaluations" / "environment" / "local-machine.json",
    )
    parser.add_argument("--disk-path", default="D:\\")
    args = parser.parse_args(argv)
    env = collect_runtime_environment(args.disk_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(env.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Selected runtime: {env.selected_inference_runtime}")
    print(f"Selected precision: {env.selected_precision}")
    print(f"Rationale: {env.selection_rationale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
