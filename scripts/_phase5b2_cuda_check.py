#!/usr/bin/env python3
import base64
import json
import os
import subprocess
import time
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
for i in range(20):
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
            "echo ssh_ok",
        ],
        capture_output=True,
        text=True,
        timeout=40,
    )
    if r.returncode == 0 and "ssh_ok" in r.stdout:
        print("ssh_ok")
        break
    print("wait", i)
    time.sleep(5)

script = r"""
set -e
which python3
python3 - <<'PY'
import torch
print('sys', torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print('sys_gpu', torch.cuda.get_device_name(0))
PY
source /workspace/.venv-qwen-cloud/bin/activate
python - <<'PY'
import torch
print('venv', torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print('venv_gpu', torch.cuda.get_device_name(0))
else:
    print('venv_gpu', 'unavailable')
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
print(r.stderr[-1000:])
raise SystemExit(r.returncode)
