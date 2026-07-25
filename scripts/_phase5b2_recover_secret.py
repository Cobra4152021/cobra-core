#!/usr/bin/env python3
"""Recover COBRA_CORE_AUTH_SECRET from running Core process env. Never prints secret."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/diagnostics/phase-5b2-live-staging"
SSH_KEY = Path.home() / ".runpod/ssh/runpodctl-ssh-key"
DEST = Path(tempfile.gettempdir()) / "phase5b2-cobra-core-auth.secret"

REMOTE_PY = r"""
import os, json, urllib.request
pid = None
for name in os.listdir('/proc'):
    if not name.isdigit():
        continue
    try:
        cmd = open(f'/proc/{name}/cmdline','rb').read().replace(b'\0', b' ').decode('utf-8','replace')
    except Exception:
        continue
    if 'cobra_core.protocol_v1' in cmd:
        pid = int(name)
        break
if not pid:
    raise SystemExit('no_pid')
env = open(f'/proc/{pid}/environ','rb').read().split(b'\0')
secret = None
for item in env:
    if item.startswith(b'COBRA_CORE_AUTH_SECRET='):
        secret = item.split(b'=',1)[1].decode()
        break
if not secret:
    raise SystemExit('no_secret')
open('/tmp/cc_secret_once.txt','w').write(secret)
req = urllib.request.Request(
    'http://127.0.0.1:18080/health',
    headers={'Authorization': f'Bearer {secret}'},
)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())
print('PID', pid)
print('HEALTH', data.get('status'), data.get('protocolVersion'), data.get('model'))
print('SECRET_BYTES', len(secret))
"""


def main() -> int:
    meta = json.loads((OUT / "pod-meta.json").read_text(encoding="utf-8"))
    keep = json.loads((OUT / "keep-active.json").read_text(encoding="utf-8"))
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
    if not ip or not port:
        print("missing ssh endpoint", flush=True)
        return 2
    b64 = base64.b64encode(REMOTE_PY.encode()).decode()
    ssh = [
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
        f"echo {b64} | base64 -d | python3",
    ]
    r = subprocess.run(ssh, capture_output=True, text=True, timeout=120)
    print("ssh_rc", r.returncode, flush=True)
    print("ssh_stdout", (r.stdout or "").strip() or "<empty>", flush=True)
    if r.returncode != 0:
        print("recover_remote_failed", (r.stderr or "")[-500:], flush=True)
        return 1
    scp = [
        "scp",
        "-i",
        str(SSH_KEY),
        "-P",
        str(port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        f"root@{ip}:/tmp/cc_secret_once.txt",
        str(DEST),
    ]
    r2 = subprocess.run(scp, capture_output=True, text=True, timeout=60)
    if r2.returncode != 0 or not DEST.exists() or DEST.stat().st_size < 8:
        print("scp_failed", r2.returncode, (r2.stderr or "")[-300:], flush=True)
        return 1
    subprocess.run(
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
            "rm -f /tmp/cc_secret_once.txt",
        ],
        capture_output=True,
        timeout=60,
    )
    print(
        "secret_bytes",
        DEST.stat().st_size,
        "path",
        str(DEST),
        "base",
        keep.get("base_url"),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
