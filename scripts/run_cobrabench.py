#!/usr/bin/env python3
"""Run CobraBench against a local model manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.evaluation.cobrabench_run import run_cobrabench  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to model manifest JSON",
    )
    parser.add_argument(
        "--model-slug",
        required=True,
        help="Slug for results directory (e.g. qwen3-8b)",
    )
    parser.add_argument(
        "--benchmark-version",
        default="0.1",
        help="Frozen CobraBench release version (default: 0.1)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run id (default: generated timestamp id)",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=None,
        dest="case_ids",
        help="Run only specific case id (repeatable)",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=512,
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=123,
    )
    parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Enable Qwen thinking mode (disabled by default for baseline protocol)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write prompts and run scaffolding only (no model load)",
    )
    args = parser.parse_args(argv)

    run_dir = run_cobrabench(
        manifest_path=args.manifest,
        model_slug=args.model_slug,
        benchmark_version=args.benchmark_version,
        run_id=args.run_id,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        seed=args.seed,
        enable_thinking=args.enable_thinking,
        case_ids=args.case_ids,
        dry_run=args.dry_run,
    )
    print(str(run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
