#!/usr/bin/env python3
"""Run technical smoke tests against an acquired local model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.inference.engine import LocalInferenceEngine  # noqa: E402
from cobra_core.providers.qwen_local import QwenLocalAdapter  # noqa: E402
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402
from cobra_core.smoke.suite import run_smoke_suite  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "model-cards" / "qwen" / "qwen3-8b.manifest.json",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=ROOT / "evaluations" / "results" / "smoke",
    )
    parser.add_argument(
        "--environment",
        type=Path,
        default=ROOT / "evaluations" / "environment" / "local-machine.json",
    )
    parser.add_argument("--no-4bit", action="store_true")
    args = parser.parse_args(argv)

    manifest = ModelManifest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
    if manifest.acquisition_status.value != "acquired":
        print("ERROR: manifest is not acquired/verified", file=sys.stderr)
        return 2

    adapter = QwenLocalAdapter(load_in_4bit=not args.no_4bit)
    engine = LocalInferenceEngine(adapter)
    env_ref = str(args.environment) if args.environment.exists() else None
    suite = run_smoke_suite(
        engine,
        manifest=manifest,
        manifest_ref=str(args.manifest),
        results_dir=args.results_dir,
        environment_reference=env_ref,
    )
    adapter.unload()
    out = args.results_dir / "smoke-summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(suite.to_dict(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(suite.to_dict(), indent=2))
    return 0 if suite.passed_count == len(suite.results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
