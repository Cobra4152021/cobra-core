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
for d in "" "0" "1"; do
  echo "TRY CUDA_VISIBLE_DEVICES='$d'"
  export CUDA_VISIBLE_DEVICES="$d"
  python3 - <<'PY'
import os, torch
print('env', os.environ.get('CUDA_VISIBLE_DEVICES'))
print('avail', torch.cuda.is_available(), 'count', torch.cuda.device_count())
try:
    x=torch.zeros(1, device='cuda')
    print('alloc_ok', x.device, torch.cuda.get_device_name(0))
except Exception as e:
    print('alloc_fail', type(e).__name__, str(e)[:160])
PY
done
# symlink nvidia0 -> nvidia1 if missing
if [ ! -e /dev/nvidia0 ] && [ -e /dev/nvidia1 ]; then
  ln -sf /dev/nvidia1 /dev/nvidia0 || true
  echo linked_nvidia0
  unset CUDA_VISIBLE_DEVICES
  python3 - <<'PY'
import torch
print('after_link', torch.cuda.is_available(), torch.cuda.device_count())
try:
  print(torch.zeros(1, device='cuda').device, torch.cuda.get_device_name(0))
except Exception as e:
  print('fail', e)
PY
fi
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
    timeout=180,
)
print(r.stdout)
print(r.stderr[-1000:])
