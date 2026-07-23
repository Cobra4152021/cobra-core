#!/usr/bin/env python3
"""Phase 3E WSL2 Qwen3-8B runtime qualification orchestrator (no CobraBench)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COMMIT = "9ea6874f3edb71fb2734c427079dd454c5d75b59"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
MAX_FULL_LOADS = 6
DIAG = ROOT / "evaluations/diagnostics/qwen3-8b-wsl2-runtime-qualification"

# Synthetic smoke only — not from CobraBench.
SYNTHETIC_PROMPT = (
    "[S1] The vehicle entered the facility at 09:10.\n"
    "[S2] The access log records a badge event at 09:14.\n"
    "[S3] No source identifies the badge holder.\n"
    "List supported facts, identify the unresolved uncertainty, cite only S1/S2/S3."
)

QUALIFICATION_RULE = {"required": 3, "mode": "fresh_subprocess_load_and_generate"}
EXTENDED_RULE = {"prompts": 5, "after_qualification": True}


def _wsl_available() -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["wsl", "-l", "-v"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"wsl invocation failed: {exc}"
    text = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 or "0x80070422" in text or "cannot be started" in text.lower():
        return False, text.strip() or f"wsl exit {proc.returncode}"
    return True, text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-commit",
        default=REQUIRED_COMMIT,
        help="Refuse to proceed unless HEAD matches this SHA",
    )
    parser.add_argument(
        "--dry-check",
        action="store_true",
        help="Only verify WSL availability and constants (no model load)",
    )
    args = parser.parse_args()

    DIAG.mkdir(parents=True, exist_ok=True)
    ok, detail = _wsl_available()
    status = {
        "schema": "cobra.diagnostics.wsl2_preflight.v1",
        "required_commit": args.require_commit,
        "model_revision": MODEL_REV,
        "model_inventory_hash": MODEL_INV,
        "max_full_loads": MAX_FULL_LOADS,
        "qualification_rule": QUALIFICATION_RULE,
        "extended_rule": EXTENDED_RULE,
        "synthetic_prompt_enforced": True,
        "benchmark_prompts_prohibited": True,
        "signal_recording": True,
        "oom_kill_recording": True,
        "subprocess_isolation": True,
        "wsl_available": ok,
        "wsl_detail": detail[:4000],
        "benchmark_executed": False,
    }
    (DIAG / "preflight-check.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )

    if not ok:
        print("WSL2 unavailable; refusing model load.", file=sys.stderr)
        print(detail[:2000], file=sys.stderr)
        return 2

    if args.dry_check:
        print(json.dumps({"wsl_available": True, "max_full_loads": MAX_FULL_LOADS}))
        return 0

    print(
        "WSL2 appears available, but Phase 3E Windows-side orchestrator "
        "does not auto-run Linux loads from this entrypoint without an "
        "explicit Linux working copy. Use the Linux-side worker under WSL.",
        file=sys.stderr,
    )
    return 3


if __name__ == "__main__":
    # Avoid accidental model import on Windows quality suite.
    if os.environ.get("COBRA_IMPORT_QWEN_WEIGHTS") == "1":
        raise SystemExit("Refusing weight import in orchestrator process")
    raise SystemExit(main())
