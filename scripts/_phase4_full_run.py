#!/usr/bin/env python3
"""Phase 4 full run: create pod, setup, execute 46 tasks, pull, terminate."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "evaluations/model-inventory/qwen3-8b-local-inventory.json"
RUNTIME_REQ = ROOT / "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-runtime.txt"
WORKER = ROOT / "scripts/_phase4_full_worker.py"
TASKPACK = ROOT / "evaluations/diagnostics/phase-4-full/taskpack.json"
OUT = ROOT / "evaluations/diagnostics/phase-4-full"
CLOUD = ROOT / "evaluations/cloud"
SSH_KEY = Path.home() / ".runpod/ssh/runpodctl-ssh-key"
SSH_PUB = Path.home() / ".runpod/ssh/runpodctl-ssh-key.pub"
IMAGE = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
COST_CAP = 0.55


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


def remote(
    ip: str, port: int, script: str, timeout: int = 3600
) -> subprocess.CompletedProcess[bytes]:
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
    r = subprocess.run(cmd, capture_output=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", errors="replace")[-500:])


def create_pod(pub: str) -> str:
    variants = [
        {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA L4"]},
        {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA RTX A5000"]},
        {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA GeForce RTX 3090"]},
        {"cloudType": "COMMUNITY", "gpuTypeIds": ["NVIDIA A40"]},
        {
            "cloudType": "COMMUNITY",
            "gpuTypeIds": [
                "NVIDIA L4",
                "NVIDIA RTX A5000",
                "NVIDIA GeForce RTX 3090",
                "NVIDIA A40",
                "NVIDIA GeForce RTX 4090",
            ],
        },
    ]
    st, pods = api("GET", "https://rest.runpod.io/v1/pods")
    if st == 200 and isinstance(pods, list):
        running = [p for p in pods if str(p.get("desiredStatus", "")).upper() == "RUNNING"]
        if running:
            raise RuntimeError(f"refuse create: {len(running)} running")
    for v in variants:
        body = {
            "name": "cobra-phase4-full",
            "imageName": IMAGE,
            "gpuCount": 1,
            "volumeInGb": 50,
            "containerDiskInGb": 30,
            "volumeMountPath": "/workspace",
            "ports": ["22/tcp"],
            "env": {"PUBLIC_KEY": pub},
            "supportPublicIp": True,
            **v,
        }
        st, payload = api("POST", "https://rest.runpod.io/v1/pods", body)
        log(
            "create_try",
            v.get("gpuTypeIds"),
            st,
            (payload or {}).get("error") if isinstance(payload, dict) else None,
        )
        if st in (200, 201) and isinstance(payload, dict) and payload.get("id"):
            return str(payload["id"])
    raise RuntimeError("no capacity for create")


def refresh(pod_id: str) -> tuple[str, int, float, str | None]:
    st, p = api("GET", f"https://rest.runpod.io/v1/pods/{pod_id}")
    if st != 200 or not isinstance(p, dict):
        raise RuntimeError(f"get pod {st}")
    cost = float(p.get("costPerHr") or 0)
    if cost > COST_CAP:
        raise RuntimeError(f"cost {cost} > cap {COST_CAP}")
    ip = p.get("publicIp") or ""
    port = (p.get("portMappings") or {}).get("22")
    gpu = (p.get("machine") or {}).get("gpuTypeId")
    if not ip or not port:
        raise RuntimeError("missing ip/port")
    return str(ip), int(port), cost, gpu


def wait_ssh(pod_id: str) -> tuple[str, int, float, str | None]:
    # ensure PUBLIC_KEY
    pub = SSH_PUB.read_text(encoding="utf-8").strip()
    api("PATCH", f"https://rest.runpod.io/v1/pods/{pod_id}", {"env": {"PUBLIC_KEY": pub}})
    for i in range(60):
        try:
            ip, port, cost, gpu = refresh(pod_id)
        except RuntimeError as e:
            log("wait_endpoint", i, e)
            time.sleep(8)
            continue
        r = subprocess.run(
            ssh_base(ip, port) + ["echo", "ssh_ok"],
            capture_output=True,
            timeout=40,
        )
        if r.returncode == 0 and b"ssh_ok" in (r.stdout or b""):
            log("ssh_ready", ip, port, cost, gpu)
            return ip, port, cost, gpu
        log("ssh_wait", i, ip, port, r.returncode)
        time.sleep(10)
    # try bootstrap restart via stop/start
    api("POST", f"https://rest.runpod.io/v1/pods/{pod_id}/stop")
    time.sleep(8)
    api("POST", f"https://rest.runpod.io/v1/pods/{pod_id}/start")
    for _i in range(40):
        try:
            ip, port, cost, gpu = refresh(pod_id)
            r = subprocess.run(
                ssh_base(ip, port) + ["echo", "ssh_ok"],
                capture_output=True,
                timeout=40,
            )
            if r.returncode == 0 and b"ssh_ok" in (r.stdout or b""):
                return ip, port, cost, gpu
        except RuntimeError:
            pass
        time.sleep(10)
    raise RuntimeError("ssh failed")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not TASKPACK.exists():
        raise SystemExit("taskpack missing; run _phase4_build_taskpack.py")
    started = datetime.now(UTC)
    pub = SSH_PUB.read_text(encoding="utf-8").strip()
    pod_id = create_pod(pub)
    log("pod_id", pod_id)
    cost = 0.0
    gpu = None
    try:
        ip, port, cost, gpu = wait_ssh(pod_id)
        (OUT / "pod-meta.json").write_text(
            json.dumps(
                {
                    "pod_id": pod_id,
                    "gpu": gpu,
                    "cost_per_hr_usd": cost,
                    "image": IMAGE,
                    "started_at": started.isoformat(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        r = remote(
            ip,
            port,
            "mkdir -p /workspace/transfer /workspace/models /workspace/cobra-pilot /workspace/phase4-out && ls -ld /workspace/transfer",
        )
        if r.returncode != 0:
            raise RuntimeError("mkdir failed: " + r.stderr.decode("utf-8", errors="replace")[-300:])
        ip, port, cost, gpu = refresh(pod_id)
        scp_to(ip, port, INV, "/workspace/transfer/qwen3-8b-local-inventory.json")
        scp_to(ip, port, WORKER, "/workspace/cobra-pilot/_phase4_full_worker.py")
        scp_to(ip, port, RUNTIME_REQ, "/workspace/cobra-pilot/requirements-cloud-runtime.txt")
        scp_to(ip, port, TASKPACK, "/workspace/cobra-pilot/taskpack.json")

        install = f"""
set -euo pipefail
export TORCHINDUCTOR_DISABLE=1
cd /workspace
if [ ! -d .venv-qwen-cloud ]; then python3 -m venv .venv-qwen-cloud; fi
source .venv-qwen-cloud/bin/activate
python -m pip install -q --upgrade pip==25.1.1 setuptools==80.9.0 wheel==0.45.1
python -m pip install -q torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -q -r /workspace/cobra-pilot/requirements-cloud-runtime.txt
python -m pip check
if [ ! -f /workspace/models/qwen3-8b/config.json ]; then
  python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-8B', revision='{MODEL_REVISION}', local_dir='/workspace/models/qwen3-8b', local_dir_use_symlinks=False); print('model_ok')"
fi
python -c "import torch,transformers,bitsandbytes as b; print(torch.__version__, bool(torch.cuda.is_available()), torch.cuda.get_device_name(0), transformers.__version__, b.__version__)"
"""
        log("install_begin")
        ip, port, cost, gpu = refresh(pod_id)
        r = remote(ip, port, install, timeout=9000)
        (OUT / "install-stdout.txt").write_bytes(r.stdout or b"")
        (OUT / "install-stderr.txt").write_bytes(r.stderr or b"")
        log("install_rc", r.returncode)
        if r.returncode != 0:
            raise RuntimeError("install failed")

        # start worker detached
        start = """
set -euo pipefail
export TORCHINDUCTOR_DISABLE=1
export COBRA_CLOUD_MODEL_DIR=/workspace/models/qwen3-8b
export COBRA_CLOUD_INVENTORY=/workspace/transfer/qwen3-8b-local-inventory.json
export COBRA_TASKPACK=/workspace/cobra-pilot/taskpack.json
export COBRA_PILOT_OUT=/workspace/phase4-out
rm -rf /workspace/phase4-out
mkdir -p /workspace/phase4-out
nohup /workspace/.venv-qwen-cloud/bin/python /workspace/cobra-pilot/_phase4_full_worker.py > /workspace/phase4-out/worker.log 2>&1 &
echo STARTED:$!
"""
        ip, port, cost, gpu = refresh(pod_id)
        r = remote(ip, port, start, timeout=60)
        log("start", (r.stdout or b"").decode("utf-8", errors="replace"))

        for i in range(180):
            ip, port, cost, gpu = refresh(pod_id)
            st = remote(
                ip,
                port,
                "if [ -f /workspace/phase4-out/RUN.json ]; then echo DONE; "
                "elif [ -f /workspace/phase4-out/run_partial.json ]; then echo PARTIAL; "
                "ls /workspace/phase4-out/tasks 2>/dev/null | wc -l; "
                "else echo WAIT; fi; pgrep -c -f _phase4_full_worker.py || true",
                timeout=60,
            )
            msg = (st.stdout or b"").decode("utf-8", errors="replace")
            log("poll", i, msg.replace("\n", " | ")[:240])
            if "DONE" in msg:
                break
            time.sleep(20)
        else:
            raise RuntimeError("timeout waiting for RUN.json")

        dest = OUT / "remote"
        dest.mkdir(parents=True, exist_ok=True)
        ip, port, cost, gpu = refresh(pod_id)
        pull = [
            "scp",
            "-i",
            str(SSH_KEY),
            "-P",
            str(port),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-r",
            f"root@{ip}:/workspace/phase4-out",
            str(dest),
        ]
        pr = subprocess.run(pull, capture_output=True, timeout=900)
        if pr.returncode != 0:
            raise RuntimeError(pr.stderr.decode("utf-8", errors="replace")[-500:])
        log("pulled_ok")
    finally:
        ended = datetime.now(UTC)
        hours = (ended - started).total_seconds() / 3600.0
        dst, _ = api("DELETE", f"https://rest.runpod.io/v1/pods/{pod_id}")
        time.sleep(3)
        _, pods = api("GET", "https://rest.runpod.io/v1/pods")
        remain = (
            [p.get("id") for p in pods if isinstance(pods, list) and p.get("id") == pod_id]
            if isinstance(pods, list)
            else []
        )
        cost_rec = {
            "schema": "cobra.cloud.cost_record.v1",
            "phase": "4-full",
            "status": "terminated" if dst in (200, 204) else f"delete_{dst}",
            "provider": "RunPod",
            "pod_id": pod_id,
            "gpu": gpu,
            "hourly_rate_at_launch_usd": cost,
            "launch_timestamp": started.isoformat(),
            "termination_timestamp": ended.isoformat(),
            "billed_or_estimated_duration_hours": round(hours, 4),
            "estimated_compute_cost_usd": round(hours * float(cost or 0), 4),
            "approved_spending_ceiling_usd": 10.0,
            "delete_http_status": dst,
            "remaining_matching_pod_ids": remain,
        }
        (OUT / "cost-record.json").write_text(
            json.dumps(cost_rec, indent=2) + "\n", encoding="utf-8"
        )
        (CLOUD / "phase4-full-cost-record.json").write_text(
            json.dumps(cost_rec, indent=2) + "\n", encoding="utf-8"
        )
        log(
            "terminated",
            dst,
            "cost",
            cost_rec["estimated_compute_cost_usd"],
            "hours",
            round(hours, 4),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
