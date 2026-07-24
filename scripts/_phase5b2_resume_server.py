#!/usr/bin/env python3
"""Resume Phase 5B.2 Core server start on an already-provisioned pod."""

from __future__ import annotations

import base64
import json
import os
import secrets
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/diagnostics/phase-5b2-live-staging"
SSH_KEY = Path.home() / ".runpod/ssh/runpodctl-ssh-key"
CORE_COMMIT = "00e4862b90d0eca0f6ec0b5f7191ba0ce43fa6fa"


def log(*a: object) -> None:
    print(*a, flush=True)


def api(method: str, url: str, body: dict | None = None):
    key = os.environ["RUNPOD_API_KEY"].strip()
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def ssh_base(ip: str, port: int) -> list[str]:
    return [
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
    ]


def remote(ip: str, port: int, script: str, timeout: int = 1200):
    b64 = base64.b64encode(script.encode()).decode()
    return subprocess.run(
        ssh_base(ip, port) + [f"echo {b64} | base64 -d | bash -s"],
        capture_output=True,
        timeout=timeout,
    )


def http_json(method, url, *, token=None, body=None, request_id=None, timeout=300):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if request_id:
        headers["x-request-id"] = request_id
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode()), dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw), dict(e.headers)
        except json.JSONDecodeError:
            return e.code, {"raw": raw[:200]}, {}


def main() -> int:
    meta = json.loads((OUT / "pod-meta.json").read_text(encoding="utf-8"))
    pod_id = meta["pod_id"]
    p = api("GET", f"https://rest.runpod.io/v1/pods/{pod_id}")
    ip = p["publicIp"]
    port = int(p["portMappings"]["22"])
    cost = float(p.get("costPerHr") or 0)
    gpu = (p.get("machine") or {}).get("gpuTypeId")
    base_url = f"https://{pod_id}-8080.proxy.runpod.net"
    revision = f"phase-5b2-{CORE_COMMIT[:12]}"
    auth_secret = (os.environ.get("COBRA_CORE_AUTH_SECRET") or "").strip() or secrets.token_urlsafe(32)
    os.environ["COBRA_CORE_AUTH_SECRET"] = auth_secret
    secret_b64 = base64.b64encode(auth_secret.encode()).decode()

    # Soft CUDA rebind + ensure deps
    prep = r"""
set -euo pipefail
source /workspace/.venv-qwen-cloud/bin/activate
python - <<'PY'
import torch
print('cuda_available', torch.cuda.is_available())
if torch.cuda.is_available():
    print('gpu', torch.cuda.get_device_name(0))
else:
    print('gpu', 'unavailable_at_probe')
PY
command -v socat >/dev/null || (apt-get update -y && apt-get install -y socat)
test -f /workspace/models/qwen3-8b/config.json
test -d /workspace/cobra-core/src/cobra_core
"""
    r = remote(ip, port, prep, timeout=300)
    log("prep_rc", r.returncode, (r.stdout or b"")[-300:])
    if r.returncode != 0:
        log("prep_stderr", (r.stderr or b"")[-500:])
        return 1

    start = f"""
set -euo pipefail
export TORCHINDUCTOR_DISABLE=1
source /workspace/.venv-qwen-cloud/bin/activate
pkill -f 'cobra_core.protocol_v1' || true
pkill -f 'socat TCP-LISTEN:8080' || true
export COBRA_CORE_AUTH_SECRET="$(echo {secret_b64} | base64 -d)"
export COBRA_INFERENCE_MODE=local
export COBRA_CORE_MODEL=cobra-core-qwen3-8b
export COBRA_CORE_REVISION='{revision}'
export COBRA_CORE_GIT_SHA='{CORE_COMMIT}'
export COBRA_CORE_TIMEOUT_MS=120000
export COBRA_CORE_MAX_CONTEXT=8192
export COBRA_CORE_MAX_OUTPUT_TOKENS=256
export COBRA_CORE_HOST=127.0.0.1
export COBRA_CORE_PORT=18080
export COBRA_PROTOCOL_VERSION=1
export COBRA_COMPATIBILITY_VERSION=1
export COBRA_CORE_EAGER_LOAD=true
export COBRA_CORE_LOG_LEVEL=INFO
export PYTHONPATH=/workspace/cobra-core/src
cd /workspace/cobra-core
nohup python -m cobra_core.protocol_v1.cli > /workspace/logs/protocol-v1.log 2>&1 &
echo SERVER_PID:$!
sleep 3
nohup socat TCP-LISTEN:8080,fork,reuseaddr TCP:127.0.0.1:18080 > /workspace/logs/socat.log 2>&1 &
echo SOCAT_PID:$!
for i in $(seq 1 120); do
  code=$(curl -s -o /tmp/h.json -w '%{{http_code}}' -H "Authorization: Bearer $COBRA_CORE_AUTH_SECRET" http://127.0.0.1:18080/health || true)
  if [ "$code" = "200" ] && grep -q '"reason":"ok"' /tmp/h.json; then
    echo HEALTH_OK:$i
    cat /tmp/h.json | head -c 400
    exit 0
  fi
  echo WAIT:$i:$code
  sleep 10
done
echo HEALTH_TIMEOUT
tail -n 120 /workspace/logs/protocol-v1.log || true
exit 1
"""
    log("starting_server")
    r = remote(ip, port, start, timeout=1500)
    out = (r.stdout or b"").replace(auth_secret.encode(), b"[REDACTED]")
    err = (r.stderr or b"").replace(auth_secret.encode(), b"[REDACTED]")
    (OUT / "server-start-stdout.txt").write_bytes(out)
    (OUT / "server-start-stderr.txt").write_bytes(err)
    log("start_rc", r.returncode)
    log(out[-500:].decode("utf-8", errors="replace"))
    if r.returncode != 0:
        return 1

    # Direct checks
    results = []
    st, body, _ = http_json("GET", f"{base_url}/health", token=auth_secret, request_id="cc_resume_h")
    results.append({"health": st, "reason": body.get("reason"), "protocolVersion": body.get("protocolVersion")})
    st2, body2, _ = http_json(
        "POST",
        f"{base_url}/v1/chat/completions",
        token=auth_secret,
        request_id="cc_resume_c",
        body={
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 32,
            "messages": [{"role": "user", "content": "Reply with exactly: pong"}],
        },
        timeout=300,
    )
    text = (((body2.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
    results.append({"completion": st2, "chars": len(str(text)), "usage": body2.get("usage")})
    (OUT / "direct-core-results.json").write_text(json.dumps({"base_url": base_url, "results": results}, indent=2) + "\n")
    (OUT / "connection-handoff.json").write_text(
        json.dumps(
            {
                "COBRA_CORE_BASE_URL": base_url,
                "COBRA_CORE_MODEL": "cobra-core-qwen3-8b",
                "COBRA_CORE_REVISION": revision,
                "COBRA_CORE_GIT_SHA": CORE_COMMIT,
                "COBRA_CORE_TIMEOUT_MS": "120000",
                "COBRA_CORE_MAX_CONTEXT": "8192",
                "COBRA_CORE_MAX_OUTPUT_TOKENS": "256",
                "COBRA_CORE_ENABLED": "true",
                "COBRA_CORE_ADMIN_ONLY": "true",
                "COBRA_CORE_SHADOW_MODE": "false",
                "auth_secret_in_process_env": True,
                "tls_method": "RunPod HTTPS proxy",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "core-ready.json").write_text(
        json.dumps(
            {
                "ready": st == 200 and st2 == 200,
                "pod_id": pod_id,
                "base_url": base_url,
                "gpu": gpu,
                "cost_per_hr_usd": cost,
                "revision": revision,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "pod-meta.json").write_text(
        json.dumps(
            {
                **meta,
                "gpu": gpu or meta.get("gpu"),
                "cost_per_hr_usd": cost,
                "proxy_base_url": base_url,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    log("CORE_READY" if st == 200 and st2 == 200 else "CORE_NOT_READY", base_url, st, st2)
    return 0 if st == 200 and st2 == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
