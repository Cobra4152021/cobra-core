"""CLI entrypoints for validation and report templates."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cobra_core.benchmarks.v02_validate import validate_v02_suite
from cobra_core.evaluation.report_template import write_empty_report_template
from cobra_core.schemas.benchmark import BenchmarkCase
from cobra_core.schemas.manifest import ModelManifest
from cobra_core.validation import validate_json_dir


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def validate_cases_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CobraBench case JSON files")
    parser.add_argument(
        "--cases-dir",
        type=Path,
        default=_repo_root() / "benchmarks" / "cases",
        help="Directory containing benchmark case JSON files",
    )
    parser.add_argument(
        "--also-validate-release",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also validate the frozen cobrabench-v0.1 release cases directory",
    )
    parser.add_argument(
        "--also-validate-v02-rc1",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also validate cobrabench-v0.2-rc1 release candidate cases",
    )
    parser.add_argument(
        "--also-validate-v02-rc2",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also validate cobrabench-v0.2-rc2 release candidate cases",
    )
    args = parser.parse_args(argv)
    cases, issues = validate_json_dir(args.cases_dir, BenchmarkCase)
    if args.also_validate_release:
        release_dir = _repo_root() / "benchmarks" / "releases" / "cobrabench-v0.1" / "cases"
        release_cases, release_issues = validate_json_dir(release_dir, BenchmarkCase)
        cases.extend(release_cases)
        issues.extend(release_issues)
    v02_bits: list[str] = []
    for flag, slug in (
        (args.also_validate_v02_rc1, "cobrabench-v0.2-rc1"),
        (args.also_validate_v02_rc2, "cobrabench-v0.2-rc2"),
    ):
        if not flag:
            continue
        rc_dir = _repo_root() / "benchmarks" / "releases" / slug / "cases"
        if not rc_dir.is_dir():
            continue
        v02_errors = validate_v02_suite(rc_dir, repo_root=_repo_root())
        for err in v02_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        if v02_errors:
            return 1
        v02_bits.append(f"{len(list(rc_dir.glob('*.json')))} {slug} case(s)")
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}", file=sys.stderr)
        print(f"Failed: {len(issues)} issue(s); {len(cases)} valid case(s).", file=sys.stderr)
        return 1
    extra = (" and " + ", ".join(v02_bits)) if v02_bits else ""
    print(f"OK: validated {len(cases)} v0.1/bench case(s){extra}")
    return 0


def validate_manifests_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate model manifest JSON files")
    parser.add_argument(
        "--manifests-dir",
        type=Path,
        default=_repo_root() / "model-cards",
        help="Directory containing ModelManifest JSON files",
    )
    args = parser.parse_args(argv)
    manifests, issues = validate_json_dir(
        args.manifests_dir,
        ModelManifest,
        recursive=True,
    )
    # Allow empty model-cards before intake, but fail hard on malformed files.
    malformed = [i for i in issues if "no files matching" not in i.message]
    if malformed:
        for issue in malformed:
            print(f"ERROR: {issue}", file=sys.stderr)
        return 1
    if not manifests:
        print(f"OK: no manifests yet in {args.manifests_dir}")
        return 0
    print(f"OK: validated {len(manifests)} model manifest(s) in {args.manifests_dir}")
    return 0


def report_template_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write an empty evaluation report template")
    parser.add_argument(
        "--output",
        type=Path,
        default=_repo_root() / "evaluations" / "reports" / "TEMPLATE.md",
        help="Output path for the empty report template",
    )
    args = parser.parse_args(argv)
    path = write_empty_report_template(args.output)
    print(f"Wrote empty evaluation report template to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate_cases_main())
