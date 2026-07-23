#!/usr/bin/env python3
"""
Execute controlled Qwen3-8B evaluation against CobraBench v0.2-rc2.

Does not modify the prepared protocol, rc2 cases, or v0.1 baseline.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.benchmarks.release import load_release_cases_v02  # noqa: E402
from cobra_core.evaluation.rc2_run import (  # noqa: E402
    MANIFEST_PATH,
    PREPARED_PROTOCOL,
    RC2_INV,
    RC2_TREE,
    build_model_inventory,
    checkpoint_manifest,
    collect_preflight,
    create_run_workspace,
    execute_case,
    finalize_sha256sums,
    inventory_hash,
    make_run_id,
    tree_hash,
    write_json,
)
from cobra_core.inference.engine import LocalInferenceEngine  # noqa: E402
from cobra_core.providers.qwen_local import QwenLocalAdapter  # noqa: E402
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "-c", "safe.directory=D:/Downloads/cobra-core", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cases", type=int, default=0, help="0 means all cases")
    parser.add_argument("--run-id", type=str, default="")
    args = parser.parse_args()

    prepared = json.loads(PREPARED_PROTOCOL.read_text(encoding="utf-8"))
    if prepared.get("status") != "prepared-not-run":
        print("Prepared protocol must remain prepared-not-run", file=sys.stderr)
        return 2
    if inventory_hash(ROOT / "benchmarks/releases/cobrabench-v0.2-rc2") != RC2_INV:
        print("rc2 inventory hash mismatch", file=sys.stderr)
        return 2
    if tree_hash(ROOT / "benchmarks/releases/cobrabench-v0.2-rc2") != RC2_TREE:
        print("rc2 tree hash mismatch", file=sys.stderr)
        return 2

    preflight = collect_preflight()
    if preflight["pass_fail_status"] == "fail":
        print("Preflight failed", preflight["warnings"], file=sys.stderr)
        return 2

    manifest = ModelManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))
    inventory = build_model_inventory(manifest)
    run_id = args.run_id or make_run_id()
    code_commit = _git_sha()
    run_dir = create_run_workspace(
        run_id, code_commit=code_commit, preflight=preflight, inventory=inventory
    )

    cases = load_release_cases_v02("0.2.0-rc2")
    cases = sorted(cases, key=lambda c: c.case_id)
    if args.max_cases and args.max_cases > 0:
        cases = cases[: args.max_cases]

    engine = LocalInferenceEngine(
        QwenLocalAdapter(load_in_4bit=True, max_memory={0: "8GiB", "cpu": "14GiB"})
    )

    case_manifest: dict = {
        "run_id": run_id,
        "order": "case_id_asc",
        "cases": [],
        "started_at": datetime.now(UTC).isoformat(),
    }
    checkpoint_manifest(run_dir, case_manifest)

    completed = 0
    failed = 0
    cuda_errors = 0
    for case in cases:
        print(f"==> {case.case_id}", flush=True)
        record = execute_case(engine=engine, manifest=manifest, case=case, run_dir=run_dir)
        case_manifest["cases"].append(record)
        checkpoint_manifest(run_dir, case_manifest)
        if record["status"] == "completed":
            completed += 1
        else:
            failed += 1
            if (
                "CUDA" in str(record.get("error", ""))
                or "cuda" in str(record.get("error", "")).lower()
            ):
                cuda_errors += 1
                if cuda_errors >= 2:
                    print("Repeated CUDA instability; stopping as partial", flush=True)
                    break

    case_manifest["ended_at"] = datetime.now(UTC).isoformat()
    case_manifest["completed"] = completed
    case_manifest["failed"] = failed
    checkpoint_manifest(run_dir, case_manifest)

    run_status = (
        "completed-pending-human-review"
        if completed == len(cases) and failed == 0
        else ("partial" if completed > 0 else "failed")
    )
    protocol = json.loads((run_dir / "protocol.json").read_text(encoding="utf-8"))
    protocol["status"] = run_status
    protocol["ended_at"] = datetime.now(UTC).isoformat()
    write_json(run_dir / "protocol.json", protocol)

    # Verify prepared protocol still prepared-not-run
    prepared_now = json.loads(PREPARED_PROTOCOL.read_text(encoding="utf-8"))
    if prepared_now.get("status") != "prepared-not-run":
        print("FATAL: prepared protocol was modified", file=sys.stderr)
        return 3

    tree = finalize_sha256sums(run_dir)
    summary = {
        "run_id": run_id,
        "status": run_status,
        "completed": completed,
        "failed": failed,
        "attempted": len(case_manifest["cases"]),
        "run_tree_hash": tree,
        "label": "Experimental release-candidate evaluation — not an official CobraBench v0.2 score.",
        "not_comparable_to_v01_0840": True,
    }
    write_json(run_dir / "reports" / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if run_status.startswith("completed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
