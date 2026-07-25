#!/usr/bin/env python3
"""Probe RunPod create options for Phase 4.2 (no secrets printed)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/diagnostics/phase-4-2-pilot"
PUB = (Path.home() / ".runpod/ssh/runpodctl-ssh-key.pub").read_text(encoding="utf-8").strip()
IMAGE = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"


def try_create(body: dict) -> tuple[int, object]:
    key = os.environ["RUNPOD_API_KEY"].strip()
    req = urllib.request.Request(
        "https://rest.runpod.io/v1/pods",
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"error": raw[:500]}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    attempts = []
    variants = [
        ("community-l4", {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA L4"]}),
        ("community-a5000", {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA RTX A5000"]}),
        ("community-a40", {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA A40"]}),
        ("community-4090", {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA GeForce RTX 4090"]}),
        ("community-3090", {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA GeForce RTX 3090"]}),
        ("secure-l4", {"cloudType": "SECURE", "gpuTypeIds": ["NVIDIA L4"]}),
        ("secure-a5000", {"cloudType": "SECURE", "gpuTypeIds": ["NVIDIA RTX A5000"]}),
        ("secure-a40", {"cloudType": "SECURE", "gpuTypeIds": ["NVIDIA A40"]}),
        (
            "community-multi",
            {
                "cloudType": "COMMUNITY",
                "gpuTypeIds": [
                    "NVIDIA L4",
                    "NVIDIA RTX A5000",
                    "NVIDIA A40",
                    "NVIDIA GeForce RTX 4090",
                    "NVIDIA GeForce RTX 3090",
                    "NVIDIA RTX 4000 Ada Generation",
                    "NVIDIA A10G",
                ],
            },
        ),
    ]
    for name, extra in variants:
        body = {
            "name": f"cobra-p42-{name}"[:30],
            "imageName": IMAGE,
            "gpuCount": 1,
            "volumeInGb": 50,
            "containerDiskInGb": 30,
            "volumeMountPath": "/workspace",
            "ports": ["22/tcp"],
            "env": {"PUBLIC_KEY": PUB},
            "supportPublicIp": True,
            **extra,
        }
        st, payload = try_create(body)
        err = payload.get("error") if isinstance(payload, dict) else None
        pid = payload.get("id") if isinstance(payload, dict) else None
        attempts.append(
            {
                "name": name,
                "status": st,
                "error": err,
                "pod_id": pid,
                "cost": payload.get("costPerHr") if isinstance(payload, dict) else None,
            }
        )
        print(name, st, err or pid)
        if pid:
            (OUT / "probe-success.json").write_text(
                json.dumps(payload, indent=2)[:20000] + "\n", encoding="utf-8"
            )
            (OUT / "create-attempts.json").write_text(
                json.dumps(attempts, indent=2) + "\n", encoding="utf-8"
            )
            return 0
    (OUT / "create-attempts.json").write_text(
        json.dumps(attempts, indent=2) + "\n", encoding="utf-8"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
