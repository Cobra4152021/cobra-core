#!/usr/bin/env python3
import json
import os
import subprocess
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "evaluations/diagnostics/phase-5b2-live-staging"
meta = json.loads((OUT / "pod-meta.json").read_text(encoding="utf-8"))
pod = meta["pod_id"]
key = os.environ["RUNPOD_API_KEY"].strip()
req = urllib.request.Request(
    f"https://rest.runpod.io/v1/pods/{pod}",
    headers={"Authorization": f"Bearer {key}"},
)
p = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
ip = p["publicIp"]
port = int(p["portMappings"]["22"])
keyfile = str(Path.home() / ".runpod/ssh/runpodctl-ssh-key")
remote = (
    "ps aux | grep -E 'protocol_v1|socat|python' | grep -v grep; echo ---; "
    "tail -n 100 /workspace/logs/protocol-v1.log 2>/dev/null || echo no_log; echo ---; "
    "curl -s -o /tmp/h.json -w '%{http_code}' http://127.0.0.1:18080/health || true; echo; "
    "head -c 500 /tmp/h.json 2>/dev/null || true"
)
cmd = [
    "ssh",
    "-i",
    keyfile,
    "-p",
    str(port),
    "-o",
    "StrictHostKeyChecking=no",
    "-o",
    "UserKnownHostsFile=/dev/null",
    f"root@{ip}",
    remote,
]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
print(r.stdout)
print(r.stderr[-500:])
raise SystemExit(r.returncode)
