#!/usr/bin/env python3
import base64
import json
import os
import subprocess
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "evaluations/diagnostics/phase-5b2-live-staging"
meta = json.loads((OUT / "pod-meta.json").read_text(encoding="utf-8"))
key = os.environ["RUNPOD_API_KEY"].strip()
req = urllib.request.Request(
    f"https://rest.runpod.io/v1/pods/{meta['pod_id']}",
    headers={"Authorization": f"Bearer {key}"},
)
p = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
ip = p["publicIp"]
port = int(p["portMappings"]["22"])
keyfile = str(Path.home() / ".runpod/ssh/runpodctl-ssh-key")
script = r"""
ls -la /dev/nvidia* 2>/dev/null || echo no_nvidia_dev
echo ---
export CUDA_VISIBLE_DEVICES=0
python3 - <<'PY'
import os, torch
print('visible', os.environ.get('CUDA_VISIBLE_DEVICES'))
print('count', torch.cuda.device_count())
try:
    torch.zeros(1, device='cuda')
    print('alloc_ok')
except Exception as e:
    print('alloc_fail', type(e).__name__, e)
PY
"""
b64 = base64.b64encode(script.encode()).decode()
r = subprocess.run(
    [
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
        f"echo {b64} | base64 -d | bash -s",
    ],
    capture_output=True,
    text=True,
    timeout=120,
)
print(r.stdout)
print(r.stderr[-800:])
