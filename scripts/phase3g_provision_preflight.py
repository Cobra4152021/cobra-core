#!/usr/bin/env python3
"""Phase 3G provisioning preflight gates (no pod create by default; no secrets printed)."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "evaluations/cloud/authorization-record.json"
IMAGE_PIN = ROOT / "evaluations/environments/cloud-qwen3-runtime/container-image-pin.json"
OUT = ROOT / "evaluations/cloud/provision-preflight.json"


def log(*args: object) -> None:
    print(*args, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pod-id", default="", help="Optional existing pod to inspect")
    parser.add_argument(
        "--allow-create-check",
        action="store_true",
        help="Evaluate create gates only; still does not create a pod",
    )
    args = parser.parse_args()

    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    image = json.loads(IMAGE_PIN.read_text(encoding="utf-8"))
    cred = bool((os.environ.get("RUNPOD_API_KEY") or "").strip())

    report: dict = {
        "schema": "cobra.cloud.provision_preflight.v1",
        "timestamp": datetime.now(UTC).isoformat(),
        "credential_present": cred,
        "credential_source": "environment variable" if cred else "none",
        "authorized": bool(auth.get("authorized")),
        "max_active_gpu_instances": (auth.get("rules") or {}).get("max_active_gpu_instances"),
        "spending_ceiling_usd": auth.get("approved_spending_ceiling_usd"),
        "runtime_ceiling_hours": auth.get("approved_runtime_ceiling_hours"),
        "preferred_image": image.get("image_name"),
        "preferred_image_digest_amd64": image.get("digest_amd64"),
        "gates": {},
        "create_new_pod": False,
        "notes": [
            "This script never creates pods.",
            "Use --pod-id to inspect an existing instance.",
            "Model/venv must use /workspace or network volume (overlay ~30GB insufficient).",
        ],
    }

    gates = report["gates"]
    gates["authorized_true"] = bool(auth.get("authorized"))
    gates["credential_present"] = cred
    gates["single_instance_rule"] = (auth.get("rules") or {}).get("max_active_gpu_instances") == 1
    gates["spot_forbidden"] = auth.get("spot_or_interruptible") is False
    gates["image_pin_present"] = bool(image.get("digest_amd64") and image.get("image_name"))

    running = []
    if cred:
        req = urllib.request.Request(
            "https://rest.runpod.io/v1/pods",
            headers={"Authorization": f"Bearer {(os.environ.get('RUNPOD_API_KEY') or '').strip()}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            pods = json.loads(resp.read().decode())
        running = [
            p.get("id") for p in pods if str(p.get("desiredStatus", "")).upper() == "RUNNING"
        ]
        report["running_pod_ids"] = running
        report["running_count"] = len(running)
        gates["at_most_one_running"] = len(running) <= 1

        if args.pod_id:
            match = [p for p in pods if p.get("id") == args.pod_id]
            if not match:
                gates["pod_found"] = False
            else:
                p = match[0]
                gates["pod_found"] = True
                cost = float(p.get("costPerHr") or 0)
                mem = float(p.get("memoryInGb") or p.get("memory_gb") or 0)
                vol = float(p.get("volumeInGb") or 0)
                cdisk = float(p.get("containerDiskInGb") or 0)
                report["pod"] = {
                    "pod_id": p.get("id"),
                    "desired_status": p.get("desiredStatus"),
                    "cost_per_hr_usd": cost,
                    "memory_gb": mem,
                    "volume_gb": vol,
                    "container_disk_gb": cdisk,
                    "image_name": p.get("imageName") or p.get("image_name"),
                }
                gates["price_within_l4_cap_or_adopted"] = cost <= float(
                    auth.get("quoted_hourly_rate_usd") or 0.5
                )
                gates["memory_at_least_32gb"] = mem >= 32 if mem else None
                gates["storage_volume_plus_container_within_100"] = (vol + cdisk) <= 100
                gates["workspace_required_note"] = True

    if args.allow_create_check:
        report["create_gates"] = {
            "would_create": False,
            "require_zero_running": len(running) == 0,
            "prefer_image": image.get("image_name"),
            "prefer_gpu_order": ["NVIDIA L4", "NVIDIA RTX A5000"],
            "refuse_spot": True,
            "refuse_public_endpoint": True,
        }

    ok = all(
        v is True for k, v in gates.items() if k != "workspace_required_note" and v is not None
    )
    report["preflight_passed"] = ok and cred and bool(auth.get("authorized"))
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    log("preflight_passed", report["preflight_passed"])
    log("wrote", OUT.relative_to(ROOT).as_posix())
    return 0 if report["preflight_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
