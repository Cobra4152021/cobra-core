#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/diagnostics/phase-5b2-live-staging"
SSH_KEY = Path.home() / ".runpod/ssh/runpodctl-ssh-key"


def main() -> int:
    meta = json.loads((OUT / "pod-meta.json").read_text(encoding="utf-8"))
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    req = urllib.request.Request(
        f"https://rest.runpod.io/v1/pods/{meta['pod_id']}",
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        pod = json.loads(resp.read().decode())
    ip = pod.get("publicIp")
    mappings = pod.get("portMappings") or {}
    port = mappings.get("22") or mappings.get(22)
    print("endpoint", ip, port, "status", pod.get("desiredStatus"), flush=True)
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
        "ps aux | grep -E 'protocol|cloudflared|uvicorn|python' | grep -v grep; echo ---; ss -ltnp | head -20; echo ---; ls -la /workspace/logs 2>/dev/null | head; echo ---; test -f /workspace/logs/server.env && echo HAS_ENV || echo NO_ENV; ls /proc/*/environ 2>/dev/null | head",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    print("rc", r.returncode, flush=True)
    print(r.stdout or "", flush=True)
    print(r.stderr or "", flush=True)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
