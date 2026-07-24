#!/usr/bin/env python3
"""Terminate Phase 5B.2 RunPod pod and verify zero remaining."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "evaluations/diagnostics/phase-5b2-live-staging"


def api(method: str, url: str) -> tuple[int, object]:
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    req = urllib.request.Request(
        url, method=method, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return e.code, {"error": raw[:300]}


def main() -> int:
    meta_path = OUT / "core-ready.json"
    pod_meta = OUT / "pod-meta.json"
    pod_id = None
    cost = 0.0
    started = None
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        pod_id = meta.get("pod_id")
        cost = float(meta.get("cost_per_hr_usd") or 0)
    if pod_meta.exists():
        pm = json.loads(pod_meta.read_text(encoding="utf-8"))
        pod_id = pod_id or pm.get("pod_id")
        cost = cost or float(pm.get("cost_per_hr_usd") or 0)
        started = pm.get("started_at")
    if not pod_id:
        # Fallback: delete any cobra-phase5b2 pods
        st, pods = api("GET", "https://rest.runpod.io/v1/pods")
        if isinstance(pods, list):
            for p in pods:
                if str(p.get("name", "")).startswith("cobra-phase5b2"):
                    pod_id = p.get("id")
                    break
    if not pod_id:
        print("no_pod")
        (OUT / "teardown.json").write_text(
            json.dumps({"terminated_at": datetime.now(UTC).isoformat(), "no_pod": True, "zero_billable_remaining": True}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        return 0

    dst, _ = api("DELETE", f"https://rest.runpod.io/v1/pods/{pod_id}")
    time.sleep(4)
    _, pods = api("GET", "https://rest.runpod.io/v1/pods")
    remain = [p.get("id") for p in pods if isinstance(pods, list) and p.get("id") == pod_id] if isinstance(pods, list) else []
    ended = datetime.now(UTC)
    hours = 0.0
    if started:
        try:
            st_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            hours = max(0.0, (ended - st_dt).total_seconds() / 3600.0)
        except ValueError:
            hours = 0.0
    rec = {
        "pod_id": pod_id,
        "delete_status": dst,
        "still_listed": remain,
        "terminated_at": ended.isoformat(),
        "runtime_hours": hours,
        "estimated_cost_usd": round(hours * cost, 4),
        "zero_billable_remaining": len(remain) == 0,
    }
    (OUT / "teardown.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rec))
    return 0 if len(remain) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
