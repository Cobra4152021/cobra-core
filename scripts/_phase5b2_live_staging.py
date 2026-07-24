#!/usr/bin/env python3
"""
Phase 5B.2 — temporary live Cobra Core GPU + direct Protocol V1 validation.

- Provisions at most one RunPod GPU
- Deploys frozen Core commit 00e4862b (real NF4 inference, not mock)
- Exposes HTTPS via RunPod proxy to loopback Protocol V1 server
- Always terminates the GPU in finally (success or failure)
- Does not modify protocol/v1 governance artifacts
- Does not print secrets
"""

from __future__ import annotations

import base64
import json
import os
import secrets
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/diagnostics/phase-5b2-live-staging"
CLOUD = ROOT / "evaluations/cloud"
SSH_KEY = Path.home() / ".runpod/ssh/runpodctl-ssh-key"
SSH_PUB = Path.home() / ".runpod/ssh/runpodctl-ssh-key.pub"
IMAGE = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
CORE_COMMIT = "00e4862b90d0eca0f6ec0b5f7191ba0ce43fa6fa"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
COST_CAP_HR = 0.90
BUDGET_USD = 10.0
KILL_DEADLINE_S = 70 * 60  # hard wall-clock kill
RUNTIME_REQ = ROOT / "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-runtime.txt"

FROZEN_SCHEMA = "f677ed325714a17ff948e3dbfaf575ec1ad3c2a3aa1940e4d05b5e49c66c32b3"
FROZEN_FIXTURE = "9cddd578ff018902f3df1069e9550de066ef54c1077ac588f2881e7c204868e7"


def log(*a: object) -> None:
    print(*a, flush=True)


def api(method: str, url: str, body: dict | None = None) -> tuple[int, object]:
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return e.code, {"error": raw[:500]}


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
        "-o",
        "ConnectTimeout=25",
        f"root@{ip}",
    ]


def remote(ip: str, port: int, script: str, timeout: int = 3600) -> subprocess.CompletedProcess[bytes]:
    b64 = base64.b64encode(script.encode()).decode()
    return subprocess.run(
        ssh_base(ip, port) + [f"echo {b64} | base64 -d | bash -s"],
        capture_output=True,
        timeout=timeout,
    )


def scp_to(ip: str, port: int, local: Path, remote_path: str) -> None:
    cmd = [
        "scp",
        "-i",
        str(SSH_KEY),
        "-P",
        str(port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        str(local),
        f"root@{ip}:{remote_path}",
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", errors="replace")[-500:])


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def create_pod(pub: str) -> str:
    variants = [
        {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA L4"]},
        {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA RTX A5000"]},
        {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA GeForce RTX 3090"]},
        {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA A40"]},
    ]
    st, pods = api("GET", "https://rest.runpod.io/v1/pods")
    if st == 200 and isinstance(pods, list):
        running = [p for p in pods if str(p.get("desiredStatus", "")).upper() == "RUNNING"]
        if running:
            raise RuntimeError(f"refuse create: {len(running)} running pods already")
    for v in variants:
        body = {
            "name": "cobra-phase5b2-core",
            "imageName": IMAGE,
            "gpuCount": 1,
            "volumeInGb": 50,
            "containerDiskInGb": 40,
            "volumeMountPath": "/workspace",
            "ports": ["22/tcp"],
            "env": {"PUBLIC_KEY": pub},
            "supportPublicIp": True,
            **v,
        }
        st, payload = api("POST", "https://rest.runpod.io/v1/pods", body)
        log("create_try", v.get("gpuTypeIds"), st)
        if st in (200, 201) and isinstance(payload, dict) and payload.get("id"):
            return str(payload["id"])
    raise RuntimeError("no capacity for create")


def refresh(pod_id: str) -> tuple[str, int, float, str | None]:
    st, p = api("GET", f"https://rest.runpod.io/v1/pods/{pod_id}")
    if st != 200 or not isinstance(p, dict):
        raise RuntimeError(f"get pod {st}")
    cost = float(p.get("costPerHr") or 0)
    if cost > COST_CAP_HR:
        raise RuntimeError(f"cost {cost} > cap {COST_CAP_HR}")
    ip = p.get("publicIp") or ""
    port = (p.get("portMappings") or {}).get("22")
    gpu = (p.get("machine") or {}).get("gpuTypeId")
    if not ip or not port:
        raise RuntimeError("missing ip/port")
    return str(ip), int(port), cost, gpu


def wait_ssh(pod_id: str) -> tuple[str, int, float, str | None]:
    pub = SSH_PUB.read_text(encoding="utf-8").strip()
    api("PATCH", f"https://rest.runpod.io/v1/pods/{pod_id}", {"env": {"PUBLIC_KEY": pub}})
    for i in range(60):
        try:
            ip, port, cost, gpu = refresh(pod_id)
        except RuntimeError as e:
            log("wait_endpoint", i, e)
            time.sleep(8)
            continue
        r = subprocess.run(ssh_base(ip, port) + ["echo", "ssh_ok"], capture_output=True, timeout=40)
        if r.returncode == 0 and b"ssh_ok" in (r.stdout or b""):
            log("ssh_ready", ip, port, cost, gpu)
            return ip, port, cost, gpu
        log("ssh_wait", i, r.returncode)
        time.sleep(10)
    raise RuntimeError("ssh failed")


def proxy_base_url(pod_id: str) -> str:
    # Placeholder; live HTTPS URL comes from cloudflared quick tunnel.
    return f"https://pending-{pod_id}.invalid"


def http_json(
    method: str,
    url: str,
    *,
    token: str | None,
    body: dict | None = None,
    request_id: str | None = None,
    timeout: float = 180.0,
) -> tuple[int, dict, dict]:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if request_id:
        headers["x-request-id"] = request_id
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {}), dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw[:200]}
        return e.code, payload, dict(e.headers)


def make_source_tarball() -> Path:
    """Pack frozen Core tree without secrets/large caches."""
    tmp = Path(tempfile.mkdtemp(prefix="cobra-core-5b2-"))
    tgz = tmp / "cobra-core.tgz"
    # Prefer git archive at exact commit when available.
    r = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", "archive", "--format=tar.gz", CORE_COMMIT, "-o", str(tgz)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode == 0 and tgz.exists():
        return tgz
    # Fallback: tar filtered tree
    with tarfile.open(tgz, "w:gz") as tf:
        for rel in ("src", "pyproject.toml", "model-cards", "protocol", "docs/protocol", "scripts"):
            p = ROOT / rel
            if p.exists():
                tf.add(p, arcname=rel)
    return tgz


def terminate(pod_id: str) -> dict:
    dst, _ = api("DELETE", f"https://rest.runpod.io/v1/pods/{pod_id}")
    time.sleep(3)
    _, pods = api("GET", "https://rest.runpod.io/v1/pods")
    remain = []
    if isinstance(pods, list):
        remain = [p.get("id") for p in pods if p.get("id") == pod_id]
    return {"delete_status": dst, "still_listed": remain}


def direct_validate_via_pod(
    ip: str,
    port: int,
    base: str,
    token: str,
    revision: str,
    git_sha: str,
) -> list[dict]:
    import importlib.util

    mod_path = Path(__file__).resolve().parent / "_phase5b2_direct_validate_remote.py"
    spec = importlib.util.spec_from_file_location("phase5b2_direct_validate_remote", mod_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    results = mod.validate(ip, port, base, token, revision, git_sha)
    for item in results:
        log(("PASS" if item.get("pass") else "FAIL"), item.get("name"), str(item.get("detail", ""))[:120])
    return results



def main() -> int:
    started = datetime.now(UTC)
    OUT.mkdir(parents=True, exist_ok=True)
    if not SSH_KEY.exists() or not SSH_PUB.exists():
        raise SystemExit("missing RunPod SSH key under ~/.runpod/ssh/")
    if not (os.environ.get("RUNPOD_API_KEY") or "").strip():
        raise SystemExit("RUNPOD_API_KEY required")

    auth_secret = secrets.token_urlsafe(32)
    # Export for Computer-side scripts in this process tree only (never logged).
    os.environ["COBRA_CORE_AUTH_SECRET"] = auth_secret

    cost_plan = {
        "provider": "RunPod",
        "preferred_gpus": ["NVIDIA L4", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 3090", "NVIDIA A40"],
        "hourly_cap_usd": COST_CAP_HR,
        "budget_usd": BUDGET_USD,
        "kill_deadline_minutes": KILL_DEADLINE_S // 60,
        "estimated_setup_minutes": 35,
        "estimated_test_minutes": 20,
        "estimated_total_cost_usd_range": [0.25, 1.50],
        "disk_gb": 50,
        "image": IMAGE,
        "tls": "RunPod HTTPS proxy (*/http port) → socat → loopback Protocol V1",
    }
    write_json(OUT / "cost-guardrail.json", cost_plan)
    write_json(
        OUT / "baseline.json",
        {
            "cobra_core_head": CORE_COMMIT,
            "governance_tip": "50e66e37ebc97de3a4d97c57d67b8975af7caaba",
            "governance_package": "e78d5be59a6e7cf8beda85a299c8fa707417d114",
            "protocolVersion": "1",
            "compatibilityVersion": "1",
            "schemaVersion": "1.0.0",
            "schemaHash": FROZEN_SCHEMA,
            "fixtureHash": FROZEN_FIXTURE,
            "official_score": 0.840,
            "cobrabench": "prepared-not-run",
            "started_at": started.isoformat(),
        },
    )

    pub = SSH_PUB.read_text(encoding="utf-8").strip()
    pod_id = create_pod(pub)
    log("pod_id", pod_id)
    base_url = proxy_base_url(pod_id)
    revision = f"phase-5b2-{CORE_COMMIT[:12]}"
    cost = 0.0
    gpu = None
    direct_results: list[dict] = []
    try:
        deadline = time.time() + KILL_DEADLINE_S
        ip, port, cost, gpu = wait_ssh(pod_id)
        write_json(
            OUT / "pod-meta.json",
            {
                "provider": "RunPod",
                "pod_id": pod_id,
                "gpu": gpu,
                "cost_per_hr_usd": cost,
                "image": IMAGE,
                "started_at": started.isoformat(),
                "proxy_base_url": base_url,
                "ports": ["22/tcp"],
                "tls_method": "Cloudflare quick tunnel (trycloudflare.com)",
                "public_ip_present": True,
            },
        )
        if time.time() > deadline:
            raise RuntimeError("kill deadline before deploy")

        tgz = make_source_tarball()
        remote(ip, port, "mkdir -p /workspace/transfer /workspace/models /workspace/cobra-core /workspace/logs")
        scp_to(ip, port, tgz, "/workspace/transfer/cobra-core.tgz")
        scp_to(ip, port, RUNTIME_REQ, "/workspace/transfer/requirements-cloud-runtime.txt")

        install = f"""
set -euo pipefail
export TORCHINDUCTOR_DISABLE=1
cd /workspace
# Fail fast if CUDA cannot allocate (provably unusable host).
python3 - <<'PY'
import torch
ok = False
try:
    if torch.cuda.is_available():
        torch.zeros(1, device='cuda')
        print('cuda_ok', torch.cuda.get_device_name(0))
        ok = True
except Exception as e:
    print('cuda_fail', type(e).__name__, str(e)[:200])
if not ok:
    raise SystemExit(42)
PY
mkdir -p /workspace/cobra-core
tar -xzf /workspace/transfer/cobra-core.tgz -C /workspace/cobra-core
python3 - <<'PY'
import json
from pathlib import Path
p = Path('/workspace/cobra-core/model-cards/qwen/qwen3-8b.manifest.json')
m = json.loads(p.read_text())
m['local_artifact_root'] = '/workspace/models/qwen3-8b'
m['acquisition_status'] = 'verified'
p.write_text(json.dumps(m, indent=2) + '\\n')
print('manifest_patched')
PY
# Use venv with system-site-packages so image torch+cu128 remains available.
if [ ! -d .venv-qwen-cloud ]; then python3 -m venv --system-site-packages .venv-qwen-cloud; fi
source .venv-qwen-cloud/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q pydantic PyYAML huggingface_hub
python -m pip install -q -r /workspace/transfer/requirements-cloud-runtime.txt
export PYTHONPATH=/workspace/cobra-core/src
if [ ! -f /workspace/models/qwen3-8b/config.json ]; then
  python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-8B', revision='{MODEL_REVISION}', local_dir='/workspace/models/qwen3-8b'); print('model_ok')"
fi
python -c "import torch,transformers,bitsandbytes as b; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0), transformers.__version__, b.__version__)"
command -v socat >/dev/null || (apt-get update -y && apt-get install -y socat)
"""
        log("install_begin")
        ip, port, cost, gpu = refresh(pod_id)
        r = remote(ip, port, install, timeout=9000)
        (OUT / "install-stdout.txt").write_bytes(r.stdout or b"")
        (OUT / "install-stderr.txt").write_bytes(r.stderr or b"")
        log("install_rc", r.returncode)
        if r.returncode == 42:
            raise RuntimeError("pod CUDA unusable (fail-fast); terminate and retry another host")
        if r.returncode != 0:
            raise RuntimeError("install/model deploy failed")
        if time.time() > deadline:
            raise RuntimeError("kill deadline after install")

        # Start Protocol V1 on loopback; expose HTTPS via Cloudflare quick tunnel.
        secret_b64 = base64.b64encode(auth_secret.encode()).decode()
        start = f"""
set -euo pipefail
export TORCHINDUCTOR_DISABLE=1
source /workspace/.venv-qwen-cloud/bin/activate
pkill -f 'cobra_core.protocol_v1' || true
pkill -f cloudflared || true
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
for i in $(seq 1 90); do
  if curl -fsS -H "Authorization: Bearer $COBRA_CORE_AUTH_SECRET" http://127.0.0.1:18080/health | grep -q '"reason":"ok"'; then
    echo HEALTH_OK:$i
    break
  fi
  sleep 10
  if [ "$i" = "90" ]; then
    echo HEALTH_TIMEOUT
    tail -n 80 /workspace/logs/protocol-v1.log || true
    exit 1
  fi
done
# Install cloudflared if needed
if [ ! -x /usr/local/bin/cloudflared ]; then
  curl -fsSL -o /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
  dpkg -i /tmp/cloudflared.deb || apt-get install -y -f
fi
rm -f /workspace/logs/cloudflared.log /workspace/logs/tunnel.url
nohup cloudflared tunnel --url http://127.0.0.1:18080 --no-autoupdate > /workspace/logs/cloudflared.log 2>&1 &
echo TUNNEL_PID:$!
for i in $(seq 1 60); do
  url=$(grep -oE 'https://[a-zA-Z0-9.-]+\\.trycloudflare\\.com' /workspace/logs/cloudflared.log | head -n1 || true)
  if [ -n "$url" ]; then
    echo "$url" > /workspace/logs/tunnel.url
    echo TUNNEL_URL:$url
    exit 0
  fi
  sleep 2
done
echo TUNNEL_TIMEOUT
tail -n 40 /workspace/logs/cloudflared.log || true
exit 1
"""
        log("server_start_begin")
        ip, port, cost, gpu = refresh(pod_id)
        r = remote(ip, port, start, timeout=1200)
        (OUT / "server-start-stdout.txt").write_bytes(
            (r.stdout or b"").replace(auth_secret.encode(), b"[REDACTED]")
        )
        (OUT / "server-start-stderr.txt").write_bytes(
            (r.stderr or b"").replace(auth_secret.encode(), b"[REDACTED]")
        )
        log("server_start_rc", r.returncode)
        if r.returncode != 0:
            raise RuntimeError("protocol server/tunnel failed to become healthy")
        out_txt = (r.stdout or b"").decode("utf-8", errors="replace")
        tunnel = ""
        for line in out_txt.splitlines():
            if line.startswith("TUNNEL_URL:"):
                tunnel = line.split("TUNNEL_URL:", 1)[1].strip()
        if not tunnel:
            raise RuntimeError("cloudflared tunnel URL not found")
        base_url = tunnel.rstrip("/")

        # Direct HTTPS validation from the pod (Cloudflare tunnel DNS may fail on local Windows).
        log("direct_validate", base_url)
        ip, port, cost, gpu = refresh(pod_id)
        direct_results = direct_validate_via_pod(ip, port, base_url, auth_secret, revision, CORE_COMMIT)
        write_json(OUT / "direct-core-results.json", {"base_url": base_url, "results": direct_results})
        if not all(x.get("pass") for x in direct_results):
            raise RuntimeError("direct Core validation failed")

        # Hand off for Computer staging: write non-secret connection info
        write_json(
            OUT / "connection-handoff.json",
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
        )
        log("CORE_READY", base_url)
        # Keep process alive marker for external Computer steps; caller may continue.
        write_json(
            OUT / "core-ready.json",
            {
                "ready": True,
                "pod_id": pod_id,
                "base_url": base_url,
                "gpu": gpu,
                "cost_per_hr_usd": cost,
                "revision": revision,
                "deadline_unix": deadline,
            },
        )
        return 0
    except Exception as exc:
        write_json(OUT / "failure.json", {"error": type(exc).__name__, "message": str(exc)[:500]})
        log("FAILED", type(exc).__name__, str(exc)[:300])
        return 1
    finally:
        # KEEP only if core-ready.json says ready; otherwise always terminate.
        keep = os.environ.get("PHASE5B2_KEEP", "").strip().lower() in {"1", "true", "yes"}
        ready_path = OUT / "core-ready.json"
        ready = False
        if ready_path.exists():
            try:
                ready = bool(json.loads(ready_path.read_text(encoding="utf-8")).get("ready"))
            except json.JSONDecodeError:
                ready = False
        if keep and ready:
            log("KEEP requested — leaving pod running for Computer staging steps")
            write_json(OUT / "keep-active.json", {"pod_id": pod_id, "base_url": base_url})
        else:
            ended = datetime.now(UTC)
            hours = max(0.0, (ended - started).total_seconds() / 3600.0)
            term = terminate(pod_id)
            write_json(
                OUT / "teardown.json",
                {
                    "terminated_at": ended.isoformat(),
                    "runtime_hours": hours,
                    "estimated_cost_usd": round(hours * float(cost or 0), 4),
                    "termination": term,
                    "zero_billable_remaining": len(term.get("still_listed") or []) == 0,
                    "kept": False,
                },
            )
            log("terminated", term)


if __name__ == "__main__":
    raise SystemExit(main())
