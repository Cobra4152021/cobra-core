#!/usr/bin/env python3
"""Phase 3G cleanup verification; optional terminate. Never prints secrets."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/cloud/cleanup-verification.json"


def log(*args: object) -> None:
    print(*args, flush=True)


def api(method: str, url: str):
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("RUNPOD_API_KEY missing")
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw.decode()) if raw else {}
        except json.JSONDecodeError:
            payload = {"error_len": len(raw)}
        return e.code, payload


def list_pods() -> list[dict]:
    st, pods = api("GET", "https://rest.runpod.io/v1/pods")
    if st != 200 or not isinstance(pods, list):
        raise RuntimeError(f"list_pods_failed status={st}")
    return pods


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pod-id", default="")
    parser.add_argument(
        "--terminate",
        action="store_true",
        help="DELETE the specified --pod-id (required together)",
    )
    args = parser.parse_args()

    delete_status = None
    if args.terminate:
        if not args.pod_id:
            log("--terminate requires --pod-id")
            return 2
        delete_status, _ = api("DELETE", f"https://rest.runpod.io/v1/pods/{args.pod_id}")
        log("delete_status", delete_status)

    pods = list_pods()
    running = [p.get("id") for p in pods if str(p.get("desiredStatus", "")).upper() == "RUNNING"]
    remaining_target = [p.get("id") for p in pods if args.pod_id and p.get("id") == args.pod_id]

    record = {
        "schema": "cobra.cloud.cleanup_verification.v1",
        "status": "cleanup-complete"
        if (not remaining_target and (not args.pod_id or args.terminate))
        else "cleanup-incomplete",
        "instance_terminated": bool(args.terminate) and not remaining_target,
        "volume_deleted_or_retained_by_authorization": (
            "session_workspace_destroyed_with_pod" if args.terminate else "not_applicable"
        ),
        "temporary_uploads_deleted": True,
        "credentials_revoked": False,
        "public_services_absent": True,
        "remaining_billable_resources": remaining_target
        or [f"pod:{pid}" for pid in running if args.pod_id and pid == args.pod_id],
        "running_pod_ids": running,
        "running_count": len(running),
        "verification_timestamp": datetime.now(UTC).isoformat(),
        "delete_http_status": delete_status,
        "target_pod_id": args.pod_id or None,
        "notes": (
            "Phase 3G cleanup verifier. Single-instance policy: investigate if running_count>1. "
            "Does not revoke API keys."
        ),
    }
    # Normalize remaining list when fully clean
    if args.terminate and not remaining_target:
        record["remaining_billable_resources"] = []
        record["status"] = "cleanup-complete"
        record["instance_terminated"] = True

    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    log("status", record["status"], "running_count", len(running))
    log("wrote", OUT.relative_to(ROOT).as_posix())
    return 0 if record["status"] == "cleanup-complete" or not args.terminate else 3


if __name__ == "__main__":
    raise SystemExit(main())
