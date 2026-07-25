#!/usr/bin/env python3
import json
import os
import subprocess
import urllib.request
from pathlib import Path

SSH_KEY = Path.home() / ".runpod/ssh/runpodctl-ssh-key"
key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
pods = json.loads(
    urllib.request.urlopen(
        urllib.request.Request(
            "https://rest.runpod.io/v1/pods", headers={"Authorization": f"Bearer {key}"}
        ),
        timeout=30,
    )
    .read()
    .decode()
)
print("pods", [(p.get("id"), p.get("desiredStatus"), p.get("costPerHr")) for p in pods])
if not pods:
    raise SystemExit(0)
pod = pods[0]
ip = pod.get("publicIp")
port = (pod.get("portMappings") or {}).get("22")
cmd = (
    "ps aux | grep -E 'protocol_v1|cloudflared|snapshot|python -m' | grep -v grep; "
    "echo ---; "
    "tail -n 40 /workspace/logs/protocol-v1.log 2>/dev/null || true; "
    "echo ---; "
    "cat /workspace/logs/tunnel.url 2>/dev/null || echo NO_TUNNEL; "
    "echo ---; "
    "test -f /workspace/models/qwen3-8b/config.json && echo HAS_MODEL || echo NO_MODEL"
)
r = subprocess.run(
    [
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
        cmd,
    ],
    capture_output=True,
    text=True,
    timeout=60,
)
print("rc", r.returncode)
print(r.stdout)
print(r.stderr[-400:])
