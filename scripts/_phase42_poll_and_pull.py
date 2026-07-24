#!/usr/bin/env python3
"""Poll pilot RUN.json, pull artifacts, terminate pod."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/diagnostics/phase-4-2-pilot"
CLOUD = ROOT / "evaluations/cloud"
SSH_KEY = Path.home() / ".runpod/ssh/runpodctl-ssh-key"
POD_ID = os.environ.get("COBRA_PILOT_POD_ID", "q5s51eej16q58m")
STARTED = datetime.now(UTC)


def api(method: str, url: str) -> tuple[int, object]:
    key = os.environ["RUNPOD_API_KEY"].strip()
    req = urllib.request.Request(
        url, method=method, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        return resp.status, (json.loads(raw) if raw else {})


def endpoint() -> tuple[str, int, float, str | None]:
    _, p = api("GET", f"https://rest.runpod.io/v1/pods/{POD_ID}")
    assert isinstance(p, dict)
    ip = p.get("publicIp")
    port = (p.get("portMappings") or {}).get("22")
    cost = float(p.get("costPerHr") or 0)
    gpu = (p.get("machine") or {}).get("gpuTypeId")
    if not ip or not port:
        raise RuntimeError("no ssh endpoint")
    return str(ip), int(port), cost, gpu


def ssh(ip: str, port: int, script: str) -> str:
    b64 = base64.b64encode(script.encode()).decode()
    cmd = [
        "ssh",
        "-i",
        str(SSH_KEY),
        "-p",
        str(port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "BatchMode=yes",
        f"root@{ip}",
        f"echo {b64} | base64 -d | bash -s",
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=90)
    out = (r.stdout or b"") + b"\n" + (r.stderr or b"")
    return out.decode("utf-8", errors="replace")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ip, port, cost, gpu = endpoint()
    print("endpoint", ip, port, cost, gpu, flush=True)

    # Ensure single worker
    print(
        ssh(
            ip,
            port,
            "pgrep -af phase42 || true; "
            "if [ ! -f /workspace/pilot-out/RUN.json ]; then "
            "  pgrep -f _phase42_pilot_worker.py >/dev/null || "
            "  (nohup /workspace/.venv-qwen-cloud/bin/python /workspace/cobra-pilot/_phase42_pilot_worker.py "
            "   >/workspace/pilot-out/worker.log 2>&1 & echo restarted:$!); "
            "fi",
        ),
        flush=True,
    )

    for i in range(80):
        ip, port, cost, gpu = endpoint()
        status = ssh(
            ip,
            port,
            "if [ -f /workspace/pilot-out/RUN.json ]; then echo DONE; "
            "elif [ -f /workspace/pilot-out/run_partial.json ]; then echo PARTIAL; "
            "wc -c /workspace/pilot-out/run_partial.json; "
            "ls /workspace/pilot-out/tasks 2>/dev/null | wc -l; "
            "else echo WAIT; fi; "
            "pgrep -c -f _phase42_pilot_worker.py || echo 0procs",
        )
        print(f"poll[{i}]", status.replace("\n", " | ")[:300], flush=True)
        if "DONE" in status:
            break
        time.sleep(20)
    else:
        raise RuntimeError("timeout waiting for RUN.json")

    dest = OUT / "remote"
    dest.mkdir(parents=True, exist_ok=True)
    ip, port, cost, gpu = endpoint()
    pull = [
        "scp",
        "-i",
        str(SSH_KEY),
        "-P",
        str(port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-r",
        f"root@{ip}:/workspace/pilot-out",
        str(dest),
    ]
    pr = subprocess.run(pull, capture_output=True)
    print("pull_rc", pr.returncode, flush=True)
    if pr.returncode != 0:
        print(pr.stderr.decode("utf-8", errors="replace")[-500:], flush=True)
        raise RuntimeError("pull failed")

    ended = datetime.now(UTC)
    # Approximate wall from pod create using probe-success if present
    hours = max((ended - STARTED).total_seconds() / 3600.0, 0.01)
    # Prefer longer estimate from pod meta if available
    meta_path = OUT / "pod-meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            launch = datetime.fromisoformat(meta["started_at"].replace("Z", "+00:00"))
            hours = (ended - launch).total_seconds() / 3600.0
        except Exception:
            pass

    dst, _ = api("DELETE", f"https://rest.runpod.io/v1/pods/{POD_ID}")
    time.sleep(3)
    _, pods = api("GET", "https://rest.runpod.io/v1/pods")
    remain = [p.get("id") for p in pods if isinstance(pods, list) and p.get("id") == POD_ID] if isinstance(pods, list) else []
    cost_rec = {
        "schema": "cobra.cloud.cost_record.v1",
        "phase": "4.2-pilot",
        "status": "terminated" if dst in (200, 204) else f"delete_{dst}",
        "provider": "RunPod",
        "pod_id": POD_ID,
        "gpu": gpu or "NVIDIA RTX A5000",
        "hourly_rate_at_launch_usd": cost,
        "launch_timestamp": STARTED.isoformat(),
        "termination_timestamp": ended.isoformat(),
        "billed_or_estimated_duration_hours": round(hours, 4),
        "estimated_compute_cost_usd": round(hours * cost, 4),
        "approved_spending_ceiling_usd": 10.0,
        "delete_http_status": dst,
        "remaining_matching_pod_ids": remain,
        "notes": "Software pins match phase-3f-qualified; host SKU A5000 (community capacity).",
    }
    (OUT / "cost-record.json").write_text(json.dumps(cost_rec, indent=2) + "\n", encoding="utf-8")
    (CLOUD / "phase42-cost-record.json").write_text(json.dumps(cost_rec, indent=2) + "\n", encoding="utf-8")
    (OUT / "pod-meta.json").write_text(
        json.dumps(
            {
                "pod_id": POD_ID,
                "public_ip": ip,
                "ssh_port": port,
                "cost_per_hr_usd": cost,
                "gpu": gpu or "NVIDIA RTX A5000",
                "image": "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404",
                "software_baseline": "phase-3f-qualified pins",
                "note": "Community L4/A40 unavailable; A5000 used for pilot",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("terminated", dst, "cost", cost_rec["estimated_compute_cost_usd"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
