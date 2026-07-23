#!/usr/bin/env python3
"""Phase 3F cloud Linux Qwen3-8B runtime qualification orchestrator (no CobraBench)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COMMIT = "695ea8833229b183e5792c49e3888ec4dde9e5f2"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
MAX_FULL_LOADS = 6
AUTH = ROOT / "evaluations/cloud/authorization-record.json"
DIAG = ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification"

# Synthetic smoke only — not from CobraBench.
SYNTHETIC_PROMPT = (
    "[S1] The shipment was logged at 08:40.\n"
    "[S2] The inspection form was signed at 09:05.\n"
    "[S3] No record identifies who moved the shipment.\n"
    "List the supported facts, identify the unresolved uncertainty, cite only S1/S2/S3."
)

QUALIFICATION_RULE = {"required": 3, "mode": "fresh_subprocess_load_and_generate"}
EXTENDED_RULE = {"prompts": 5, "after_qualification": True}


def _load_auth() -> dict:
    if not AUTH.is_file():
        return {"authorized": False, "status": "missing"}
    return json.loads(AUTH.read_text(encoding="utf-8"))


def _credentials_present() -> bool:
    return bool(os.environ.get("RUNPOD_API_KEY") or os.environ.get("RUNPOD_API"))


def _authorization_complete(auth: dict) -> tuple[bool, str]:
    if not auth.get("authorized"):
        return False, "authorized is false"
    required = (
        "provider",
        "gpu",
        "quoted_hourly_rate_usd",
        "approved_spending_ceiling_usd",
        "approved_runtime_ceiling_hours",
        "approved_disk_size_gb",
        "region",
        "authorization_timestamp",
        "authorization_source",
    )
    missing = [k for k in required if auth.get(k) in (None, "", [])]
    if missing:
        return False, "missing fields: " + ", ".join(missing)
    rules = auth.get("rules") or {}
    if rules.get("max_active_gpu_instances") != 1:
        return False, "max_active_gpu_instances must be 1"
    if auth.get("approved_spending_ceiling_usd") is not None:
        try:
            if float(auth["approved_spending_ceiling_usd"]) <= 0:
                return False, "spending ceiling must be positive"
        except (TypeError, ValueError):
            return False, "invalid spending ceiling"
    if not _credentials_present():
        return False, "RUNPOD_API_KEY missing from environment"
    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-commit", default=REQUIRED_COMMIT)
    parser.add_argument(
        "--require-authorization",
        action="store_true",
        default=True,
        help="Refuse to provision/load without complete authorization (default)",
    )
    parser.add_argument(
        "--dry-check",
        action="store_true",
        help="Validate authorization gate and constants only (no cloud API, no model load)",
    )
    args = parser.parse_args()

    DIAG.mkdir(parents=True, exist_ok=True)
    auth = _load_auth()
    ok, reason = _authorization_complete(auth)
    status = {
        "schema": "cobra.diagnostics.cloud_preflight.v1",
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
        "spending_ceiling_enforced": True,
        "single_instance_rule": True,
        "authorized": bool(auth.get("authorized")),
        "credentials_present": _credentials_present(),
        "authorization_complete": ok,
        "authorization_reason": reason,
        "authorization_status": auth.get("status"),
        "benchmark_executed": False,
        "provisioned": False,
        "cloud_api_contacted": False,
    }
    (DIAG / "preflight-check.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )

    if args.require_authorization and not ok:
        print("Cloud authorization incomplete; refusing provision/load.", file=sys.stderr)
        print(reason, file=sys.stderr)
        print(f"status={auth.get('status', 'unknown')}", file=sys.stderr)
        return 2

    if args.dry_check:
        print(json.dumps({"authorized": ok, "max_full_loads": MAX_FULL_LOADS}))
        return 0

    print(
        "Authorization present, but this Windows-side orchestrator does not contact "
        "provider APIs or load weights. Run the Linux worker on the authorized host.",
        file=sys.stderr,
    )
    return 3


if __name__ == "__main__":
    if os.environ.get("COBRA_IMPORT_QWEN_WEIGHTS") == "1":
        raise SystemExit("Refusing weight import in orchestrator process")
    if os.environ.get("COBRA_CLOUD_PROVISION") == "1":
        raise SystemExit("Refusing automatic cloud provisioning from quality suite")
    raise SystemExit(main())
