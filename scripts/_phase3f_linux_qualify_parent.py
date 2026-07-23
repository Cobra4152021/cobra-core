#!/usr/bin/env python3
"""Phase 3F Linux parent: load / generate / 3x qual / extended (max 6 full loads)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification"
WORKER = ROOT / "scripts/_phase3f_linux_qualify_worker.py"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
MAX_FULL_LOADS = 6
REQUIRED_COMMIT = "695ea8833229b183e5792c49e3888ec4dde9e5f2"


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def _git_head() -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return (r.stdout or "").strip()


def run_attempt(
    label: str, mode: str, full_load_count: list[int], artifact: Path, inventory: Path
) -> dict:
    if full_load_count[0] >= MAX_FULL_LOADS:
        raise RuntimeError("full-load ceiling reached")
    full_load_count[0] += 1
    attempt_id = f"cloud-{full_load_count[0]:02d}-{label}"
    attempt_dir = DIAG / "attempts" / attempt_id
    if attempt_dir.exists():
        raise RuntimeError(f"attempt exists: {attempt_dir}")
    attempt_dir.mkdir(parents=True)

    result_json = attempt_dir / "result.json"
    progress = attempt_dir / "progress.jsonl"
    smoke = attempt_dir / "smoke-output.txt"
    cmd = [
        sys.executable,
        str(WORKER),
        "--mode",
        mode,
        "--artifact-dir",
        str(artifact),
        "--result-json",
        str(result_json),
        "--progress-jsonl",
        str(progress),
        "--inventory-json",
        str(inventory),
        "--smoke-output",
        str(smoke),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    elapsed = round(time.perf_counter() - t0, 3)
    result = {}
    if result_json.is_file():
        result = json.loads(result_json.read_text(encoding="utf-8"))
    attempt = {
        "attempt_id": attempt_id,
        "label": label,
        "mode": mode,
        "full_load_index": full_load_count[0],
        "exit_code": proc.returncode,
        "elapsed_s": elapsed,
        "success": bool(result.get("success")) and proc.returncode == 0,
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
        "result": result,
        "benchmark_executed": False,
    }
    _write(attempt_dir / "attempt.json", attempt)
    return attempt


def main() -> int:
    DIAG.mkdir(parents=True, exist_ok=True)
    head = _git_head()
    artifact = Path(os.environ.get("COBRA_CLOUD_MODEL_DIR") or "")
    inventory = Path(os.environ.get("COBRA_CLOUD_INVENTORY") or "")
    if not artifact.is_dir():
        raise SystemExit("COBRA_CLOUD_MODEL_DIR missing")
    if not inventory.is_file():
        raise SystemExit("COBRA_CLOUD_INVENTORY missing")

    # Native backend validation
    native = subprocess.run(
        [
            sys.executable,
            "-c",
            "import torch,bitsandbytes,transformers,accelerate,psutil;"
            "assert torch.cuda.is_available();"
            "x=torch.zeros(8,device='cuda'); y=x+1;"
            "print('native_ok', torch.__version__, torch.cuda.get_device_name(0))",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    _write(
        DIAG / "native-backend-validation.json",
        {
            "success": native.returncode == 0,
            "stdout": native.stdout,
            "stderr": native.stderr[-2000:],
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
    if native.returncode != 0:
        print("NATIVE_BACKEND_FAILED", native.stderr[-1000:], flush=True)
        return 2

    summary: dict = {
        "schema": "cobra.diagnostics.cloud_qualification_summary.v1",
        "started_at": datetime.now(UTC).isoformat(),
        "required_commit": REQUIRED_COMMIT,
        "git_head": head,
        "commit_match": head == REQUIRED_COMMIT,
        "model_revision": MODEL_REV,
        "model_inventory_hash": MODEL_INV,
        "max_full_loads": MAX_FULL_LOADS,
        "benchmark_executed": False,
        "official_v01_score_unchanged": 0.84,
        "attempts": [],
        "full_loads_used": 0,
    }
    counts = [0]
    # 1) initial load
    a1 = run_attempt("load", "load", counts, artifact, inventory)
    summary["attempts"].append({"id": a1["attempt_id"], "success": a1["success"], "mode": "load"})
    if not a1["success"]:
        summary["outcome_hint"] = "D_or_E_load_failed"
        summary["full_loads_used"] = counts[0]
        summary["ended_at"] = datetime.now(UTC).isoformat()
        _write(DIAG / "qualification_summary.json", summary)
        print("FAIL initial load", flush=True)
        return 3
    # 2) initial generate
    a2 = run_attempt("gen", "generate", counts, artifact, inventory)
    summary["attempts"].append(
        {"id": a2["attempt_id"], "success": a2["success"], "mode": "generate"}
    )
    if not a2["success"]:
        summary["outcome_hint"] = "C_generate_failed"
        summary["full_loads_used"] = counts[0]
        summary["ended_at"] = datetime.now(UTC).isoformat()
        _write(DIAG / "qualification_summary.json", summary)
        print("FAIL initial generate", flush=True)
        return 4
    # 3-5) qualification runs
    qual_ok = 0
    for i in range(1, 4):
        aq = run_attempt(f"qual{i}", "generate", counts, artifact, inventory)
        summary["attempts"].append(
            {"id": aq["attempt_id"], "success": aq["success"], "mode": "qualification"}
        )
        if aq["success"]:
            qual_ok += 1
        else:
            break
    summary["qualification_passed"] = qual_ok == 3
    if qual_ok != 3:
        summary["outcome_hint"] = "C_qualification_failed"
        summary["full_loads_used"] = counts[0]
        summary["ended_at"] = datetime.now(UTC).isoformat()
        _write(DIAG / "qualification_summary.json", summary)
        print(f"FAIL qualification {qual_ok}/3", flush=True)
        return 5
    # 6) extended
    ae = run_attempt("extended", "extended", counts, artifact, inventory)
    summary["attempts"].append(
        {"id": ae["attempt_id"], "success": ae["success"], "mode": "extended"}
    )
    summary["extended_passed"] = bool(ae["success"])
    summary["full_loads_used"] = counts[0]
    summary["ended_at"] = datetime.now(UTC).isoformat()
    if ae["success"]:
        summary["outcome_hint"] = "A_fully_qualified"
        summary["status"] = "smoke-qualified"
    else:
        summary["outcome_hint"] = "C_extended_failed"
        summary["status"] = "provisionally-unstable"
    _write(DIAG / "qualification_summary.json", summary)
    print(
        "QUALIFICATION_DONE",
        summary["outcome_hint"],
        "loads",
        counts[0],
        flush=True,
    )
    return 0 if ae["success"] else 6


if __name__ == "__main__":
    raise SystemExit(main())
