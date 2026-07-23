#!/usr/bin/env python3
"""Discover running RunPod pods via REST and write adoption record (never prints secrets)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/cloud"
REST_PODS = "https://rest.runpod.io/v1/pods"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def main() -> int:
    api_key = (os.environ.get("RUNPOD_API_KEY") or os.environ.get("RUNPOD_API") or "").strip()
    cred_present = bool(api_key and len(api_key) > 8)
    cred_status = {
        "schema": "cobra.cloud.credential_status.v1",
        "credential_present": cred_present,
        "authentication_succeeded": False,
        "credential_source": "environment variable" if cred_present else "none",
        "api_used": REST_PODS,
        "timestamp": _now(),
        "notes": "Value never logged.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    if not cred_present:
        (OUT / "credential-status.json").write_text(
            json.dumps(cred_status, indent=2) + "\n", encoding="utf-8"
        )
        print("credential_present False")
        return 2

    req = urllib.request.Request(
        REST_PODS,
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            pods = json.loads(resp.read().decode("utf-8"))
        if not isinstance(pods, list):
            raise RuntimeError("unexpected_pods_payload")
        cred_status["authentication_succeeded"] = True
    except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as exc:
        (OUT / "credential-status.json").write_text(
            json.dumps(cred_status, indent=2) + "\n", encoding="utf-8"
        )
        print("authentication_succeeded False")
        print(f"auth_error_class {type(exc).__name__}")
        return 3

    (OUT / "credential-status.json").write_text(
        json.dumps(cred_status, indent=2) + "\n", encoding="utf-8"
    )

    def summarize(p: dict) -> dict:
        return {
            "pod_id": p.get("id"),
            "name": p.get("name"),
            "desired_status": p.get("desiredStatus"),
            "image_name": p.get("imageName"),
            "cost_per_hr_usd": p.get("costPerHr"),
            "gpu_count": p.get("gpuCount"),
            "volume_gb": p.get("volumeInGb"),
            "container_disk_gb": p.get("containerDiskInGb"),
            "memory_gb": p.get("memoryInGb"),
            "created_at": p.get("createdAt"),
            "last_started_at": p.get("lastStartedAt"),
            "ports": p.get("ports"),
            "port_mappings": p.get("portMappings"),
            "has_public_ip": bool(p.get("publicIp")),
        }

    summaries = [summarize(p) for p in pods]
    running = [s for s in summaries if str(s.get("desired_status", "")).upper() == "RUNNING"]

    discovery = {
        "schema": "cobra.cloud.runpod_discovery.v1",
        "api": REST_PODS,
        "timestamp": _now(),
        "authentication_succeeded": True,
        "credential_source": "environment variable",
        "total_pods_visible": len(pods),
        "running_pods_count": len(running),
        "pods": summaries,
        "running_pods": running,
    }
    (OUT / "runpod-discovery.json").write_text(
        json.dumps(discovery, indent=2) + "\n", encoding="utf-8"
    )

    adopt = running[0] if len(running) == 1 else None
    reason = (
        "single_running_pod"
        if adopt
        else ("no_running_pods" if not running else "ambiguous_multiple_running_pods")
    )
    print("credential_present True")
    print("authentication_succeeded True")
    print("running_pods", len(running))
    print("adopted", bool(adopt))
    print("reason", reason)
    if adopt:
        print("pod_id", adopt.get("pod_id"))
        print("cost_per_hr", adopt.get("cost_per_hr_usd"))
        print("memory_gb", adopt.get("memory_gb"))
        print("status", adopt.get("desired_status"))
    return 0 if adopt else 4


if __name__ == "__main__":
    raise SystemExit(main())
