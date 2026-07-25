#!/usr/bin/env python3
"""Phase 4.2: create one RunPod pod, run pilot worker, export, terminate. No secrets printed."""

from __future__ import annotations

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
IMAGE_PIN = ROOT / "evaluations/environments/cloud-qwen3-runtime/container-image-pin.json"
RUNTIME_REQ = ROOT / "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-runtime.txt"
WORKER = ROOT / "scripts/_phase42_pilot_worker.py"
OUT = ROOT / "evaluations/diagnostics/phase-4-2-pilot"
CLOUD = ROOT / "evaluations/cloud"
SSH_KEY = Path.home() / ".runpod" / "ssh" / "runpodctl-ssh-key"
SSH_PUB = Path.home() / ".runpod" / "ssh" / "runpodctl-ssh-key.pub"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"


def log(*a: object) -> None:
    print(*a, flush=True)


def api(method: str, url: str, body: dict | None = None) -> tuple[int, object]:
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("RUNPOD_API_KEY missing")
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw) if raw else {"error": str(e)}
        except json.JSONDecodeError:
            payload = {"error": raw[:500]}
        return e.code, payload


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
        "ConnectTimeout=20",
        f"root@{ip}",
    ]


def wait_ssh(ip: str, port: int, tries: int = 40) -> None:
    for i in range(tries):
        r = subprocess.run(
            ssh_base(ip, port) + ["echo", "ssh_ok"],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if r.returncode == 0 and "ssh_ok" in (r.stdout or ""):
            log("ssh_ready", ip, port)
            return
        log("ssh_wait", i + 1, r.returncode)
        time.sleep(15)
    raise RuntimeError("ssh not ready")


def scp_to(ip: str, port: int, local: Path, remote: str) -> None:
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
        f"root@{ip}:{remote}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"scp failed: {r.stderr[-500:]}")


def remote(
    ip: str, port: int, script: str, timeout: int = 3600
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ssh_base(ip, port) + ["bash", "-lc", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CLOUD.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    image = json.loads(IMAGE_PIN.read_text(encoding="utf-8"))
    pub = SSH_PUB.read_text(encoding="utf-8").strip()

    st, pods = api("GET", "https://rest.runpod.io/v1/pods")
    if st != 200:
        raise RuntimeError(f"list pods failed {st}")
    assert isinstance(pods, list)
    running = [p for p in pods if str(p.get("desiredStatus", "")).upper() == "RUNNING"]
    if running:
        raise RuntimeError(f"refusing create: already {len(running)} running pod(s)")

    # Prefer L4 then A5000; refuse if rate too high after create inspect.
    create_body = {
        "name": "cobra-phase42-pilot",
        "imageName": image.get("image_name"),
        "gpuTypeIds": ["NVIDIA L4", "NVIDIA RTX A5000", "NVIDIA A40"],
        "gpuCount": 1,
        "cloudType": "COMMUNITY",
        "volumeInGb": 50,
        "containerDiskInGb": 30,
        "volumeMountPath": "/workspace",
        "ports": ["22/tcp"],
        "env": {"PUBLIC_KEY": pub},
        "supportPublicIp": True,
    }
    log("creating_pod")
    st, pod = api("POST", "https://rest.runpod.io/v1/pods", create_body)
    (OUT / "create-response.json").write_text(
        json.dumps(pod, indent=2)[:20000] + "\n", encoding="utf-8"
    )
    if st not in (200, 201) or not isinstance(pod, dict) or not pod.get("id"):
        raise RuntimeError(
            f"create failed status={st} body_keys={list(pod) if isinstance(pod, dict) else type(pod)}"
        )
    pod_id = pod["id"]
    log("pod_id", pod_id)

    ip = None
    port = None
    cost = None
    gpu = None
    for i in range(60):
        st, p = api("GET", f"https://rest.runpod.io/v1/pods/{pod_id}")
        if st != 200 or not isinstance(p, dict):
            time.sleep(10)
            continue
        cost = float(p.get("costPerHr") or 0)
        gpu = p.get("machine", {}).get("gpuDisplayName") or p.get("gpuTypeId") or p.get("name")
        # machine may nest differently
        if isinstance(p.get("machine"), dict):
            gpu = p["machine"].get("gpuDisplayName") or gpu
        mappings = p.get("portMappings") or {}
        ip = p.get("publicIp")
        port = mappings.get("22") or mappings.get(22)
        status = p.get("desiredStatus")
        log("wait_pod", i + 1, status, "ip", bool(ip), "port", port, "cost", cost)
        if cost and cost > 0.50:
            api("DELETE", f"https://rest.runpod.io/v1/pods/{pod_id}")
            raise RuntimeError(f"cost {cost} exceeds pilot cap 0.50")
        if ip and port and str(status).upper() == "RUNNING":
            break
        time.sleep(10)
    else:
        api("DELETE", f"https://rest.runpod.io/v1/pods/{pod_id}")
        raise RuntimeError("pod not ready")

    port = int(port)
    meta = {
        "pod_id": pod_id,
        "public_ip": ip,
        "ssh_port": port,
        "cost_per_hr_usd": cost,
        "gpu": gpu,
        "image": image.get("image_name"),
        "started_at": started.isoformat(),
    }
    (OUT / "pod-meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (CLOUD / "phase42-pod-meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    try:
        wait_ssh(ip, port)
        # Bootstrap may already have PUBLIC_KEY from create; still verify.
        log("remote_setup_begin")
        setup = r"""
set -euo pipefail
mkdir -p /workspace/transfer /workspace/models /workspace/cobra-pilot
python3 --version
nvidia-smi -L || true
"""
        r = remote(ip, port, setup, timeout=120)
        log("setup_out", (r.stdout or "")[-500:], (r.stderr or "")[-300:])
        if r.returncode != 0:
            raise RuntimeError("remote setup failed")

        scp_to(ip, port, INV, "/workspace/transfer/qwen3-8b-local-inventory.json")
        scp_to(ip, port, WORKER, "/workspace/cobra-pilot/_phase42_pilot_worker.py")
        scp_to(ip, port, RUNTIME_REQ, "/workspace/cobra-pilot/requirements-cloud-runtime.txt")

        # Install venv + torch pin + runtime reqs; download pinned model revision to /workspace
        install = f"""
set -euo pipefail
cd /workspace
if [ ! -d .venv-qwen-cloud ]; then python3 -m venv .venv-qwen-cloud; fi
source .venv-qwen-cloud/bin/activate
python -m pip install -q --upgrade pip==25.1.1 setuptools==80.9.0 wheel==0.45.1
python -m pip install -q torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -q -r /workspace/cobra-pilot/requirements-cloud-runtime.txt
python -m pip check
if [ ! -f /workspace/models/qwen3-8b/config.json ]; then
  python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='Qwen/Qwen3-8B',
    revision='{MODEL_REVISION}',
    local_dir='/workspace/models/qwen3-8b',
    local_dir_use_symlinks=False,
)
print('model_download_ok')
PY
fi
python - <<'PY'
import torch, transformers, accelerate, bitsandbytes
print('torch', torch.__version__)
print('cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
print('transformers', transformers.__version__)
print('accelerate', accelerate.__version__)
print('bnb', bitsandbytes.__version__)
PY
"""
        log("install_and_model_begin")
        r = remote(ip, port, install, timeout=7200)
        (OUT / "install-stdout.txt").write_text(r.stdout or "", encoding="utf-8")
        (OUT / "install-stderr.txt").write_text(r.stderr or "", encoding="utf-8")
        log("install_rc", r.returncode)
        if r.returncode != 0:
            raise RuntimeError("install/model failed")

        run = """
set -euo pipefail
source /workspace/.venv-qwen-cloud/bin/activate
python /workspace/cobra-pilot/_phase42_pilot_worker.py
"""
        log("pilot_run_begin")
        r = remote(ip, port, run, timeout=7200)
        (OUT / "pilot-stdout.txt").write_text(r.stdout or "", encoding="utf-8")
        (OUT / "pilot-stderr.txt").write_text(r.stderr or "", encoding="utf-8")
        log("pilot_rc", r.returncode, (r.stdout or "")[-400:])
        if r.returncode != 0:
            raise RuntimeError("pilot worker failed")

        # Pull results
        local_tasks = OUT / "remote"
        local_tasks.mkdir(parents=True, exist_ok=True)
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
            f"root@{ip}:/workspace/pilot-out",
            str(local_tasks),
        ]
        pr = subprocess.run(pull, capture_output=True, text=True, timeout=600)
        if pr.returncode != 0:
            raise RuntimeError(f"pull failed: {pr.stderr[-500:]}")
        log("pulled", local_tasks)
    finally:
        ended = datetime.now(UTC)
        hours = (ended - started).total_seconds() / 3600.0
        est_cost = round(hours * float(cost or 0), 4)
        log("terminating", pod_id)
        dst, _ = api("DELETE", f"https://rest.runpod.io/v1/pods/{pod_id}")
        time.sleep(5)
        st2, pods2 = api("GET", "https://rest.runpod.io/v1/pods")
        remaining = []
        if st2 == 200 and isinstance(pods2, list):
            remaining = [
                p.get("id")
                for p in pods2
                if str(p.get("desiredStatus", "")).upper() in {"RUNNING", "EXITED", "DEAD"}
                or p.get("id") == pod_id
            ]
            # filter truly present
            remaining = [p.get("id") for p in pods2 if p.get("id") == pod_id]
        cost_rec = {
            "schema": "cobra.cloud.cost_record.v1",
            "phase": "4.2-pilot",
            "status": "terminated" if dst in (200, 204) else f"delete_status_{dst}",
            "provider": "RunPod",
            "pod_id": pod_id,
            "gpu": gpu,
            "hourly_rate_at_launch_usd": cost,
            "launch_timestamp": started.isoformat(),
            "termination_timestamp": ended.isoformat(),
            "billed_or_estimated_duration_hours": round(hours, 4),
            "estimated_compute_cost_usd": est_cost,
            "approved_spending_ceiling_usd": 10.0,
            "delete_http_status": dst,
            "remaining_matching_pod_ids": remaining,
        }
        (OUT / "cost-record.json").write_text(
            json.dumps(cost_rec, indent=2) + "\n", encoding="utf-8"
        )
        (CLOUD / "phase42-cost-record.json").write_text(
            json.dumps(cost_rec, indent=2) + "\n", encoding="utf-8"
        )
        log("cost_usd", est_cost, "hours", round(hours, 4), "delete", dst)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
