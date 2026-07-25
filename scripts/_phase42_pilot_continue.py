#!/usr/bin/env python3
"""Continue Phase 4.2 pilot on an already-created pod. Terminates at end."""

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
WORKER = ROOT / "scripts/_phase42_pilot_worker.py"
OUT = ROOT / "evaluations/diagnostics/phase-4-2-pilot"
CLOUD = ROOT / "evaluations/cloud"
SSH_KEY = Path.home() / ".runpod" / "ssh" / "runpodctl-ssh-key"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
POD_ID = os.environ.get("COBRA_PILOT_POD_ID", "aj9k9rzjyxpivp")


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
        "ConnectTimeout=20",
        f"root@{ip}",
    ]


def wait_ssh(ip_port_fn, tries: int = 50) -> tuple[str, int]:
    for i in range(tries):
        ip, port = ip_port_fn()
        r = subprocess.run(
            ssh_base(ip, port) + ["echo", "ssh_ok"],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if r.returncode == 0 and "ssh_ok" in (r.stdout or ""):
            log("ssh_ready", ip, port)
            return ip, port
        log("ssh_wait", i + 1, ip, port, r.returncode, (r.stderr or "")[-120:])
        time.sleep(12)
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
    # Base64 avoids Windows OpenSSH mangling of remote argv/paths.
    b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
    wrapped = f"echo {b64} | base64 -d | bash -s"
    return subprocess.run(
        ssh_base(ip, port) + [wrapped],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    # Ensure PUBLIC_KEY on pod
    pub = (Path.home() / ".runpod/ssh/runpodctl-ssh-key.pub").read_text(encoding="utf-8").strip()
    api("PATCH", f"https://rest.runpod.io/v1/pods/{POD_ID}", {"env": {"PUBLIC_KEY": pub}})

    def refresh() -> tuple[str, int, float, str | None]:
        st, p = api("GET", f"https://rest.runpod.io/v1/pods/{POD_ID}")
        if st != 200 or not isinstance(p, dict):
            raise RuntimeError(f"pod get failed {st}")
        c = float(p.get("costPerHr") or 0)
        machine = p.get("machine") if isinstance(p.get("machine"), dict) else {}
        g = machine.get("gpuTypeId") or machine.get("gpuDisplayName") or p.get("gpuTypeId")
        i = p.get("publicIp") or ""
        mappings = p.get("portMappings") or {}
        pt = mappings.get("22") or mappings.get(22)
        if not i or not pt:
            raise RuntimeError("missing ip/port")
        if c > 0.55:
            raise RuntimeError(f"cost {c} too high")
        return str(i), int(pt), c, g

    ip = port = cost = gpu = None
    for i in range(60):
        try:
            ip, port, cost, gpu = refresh()
            log("pod", i + 1, "cost", cost, "gpu", gpu, "ip", ip, "port", port)
            break
        except RuntimeError as exc:
            log("pod_wait", i + 1, str(exc))
            time.sleep(8)
    else:
        api("DELETE", f"https://rest.runpod.io/v1/pods/{POD_ID}")
        raise RuntimeError("pod not ready")

    def live_ssh() -> tuple[str, int]:
        i, p, _, _ = refresh()
        return i, p

    meta = {
        "pod_id": POD_ID,
        "public_ip": ip,
        "ssh_port": port,
        "cost_per_hr_usd": cost,
        "gpu": gpu,
        "started_at": started.isoformat(),
        "note": "Community capacity forced RTX 3090; software pins match phase-3f-qualified",
    }
    (OUT / "pod-meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    try:
        ip, port = wait_ssh(live_ssh)
        mr = remote(
            ip,
            port,
            "mkdir -p /workspace/transfer /workspace/models /workspace/cobra-pilot /workspace/pilot-out && ls -ld /workspace/transfer",
        )
        (OUT / "mkdir-stdout.txt").write_text(
            (mr.stdout or "") + "\n" + (mr.stderr or ""), encoding="utf-8"
        )
        if mr.returncode != 0:
            raise RuntimeError(f"mkdir failed rc={mr.returncode}")
        ip, port = live_ssh()
        scp_to(ip, port, INV, "/workspace/transfer/qwen3-8b-local-inventory.json")
        scp_to(ip, port, WORKER, "/workspace/cobra-pilot/_phase42_pilot_worker.py")
        scp_to(ip, port, RUNTIME_REQ, "/workspace/cobra-pilot/requirements-cloud-runtime.txt")

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
  python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-8B', revision='{MODEL_REVISION}', local_dir='/workspace/models/qwen3-8b', local_dir_use_symlinks=False); print('model_download_ok')"
fi
python -c "import torch,transformers,accelerate,bitsandbytes as b; print(torch.__version__, torch.cuda.get_device_name(0), transformers.__version__, accelerate.__version__, b.__version__)"
"""
        log("install_begin")
        ip, port = live_ssh()
        r = remote(ip, port, install, timeout=9000)
        (OUT / "install-stdout.txt").write_text(r.stdout or "", encoding="utf-8")
        (OUT / "install-stderr.txt").write_text(r.stderr or "", encoding="utf-8")
        log("install_rc", r.returncode)
        if r.returncode != 0:
            raise RuntimeError("install failed")

        log("pilot_begin")
        ip, port = live_ssh()
        r = remote(
            ip,
            port,
            "source /workspace/.venv-qwen-cloud/bin/activate && python /workspace/cobra-pilot/_phase42_pilot_worker.py",
            timeout=9000,
        )
        (OUT / "pilot-stdout.txt").write_text(r.stdout or "", encoding="utf-8")
        (OUT / "pilot-stderr.txt").write_text(r.stderr or "", encoding="utf-8")
        log("pilot_rc", r.returncode, (r.stdout or "")[-500:])
        if r.returncode != 0:
            raise RuntimeError("pilot failed")

        local_tasks = OUT / "remote"
        local_tasks.mkdir(parents=True, exist_ok=True)
        ip, port = live_ssh()
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
            raise RuntimeError(f"pull failed {pr.stderr[-400:]}")
        log("pulled_ok")
    except Exception:
        # Keep pod for retry unless explicitly forcing cleanup via env.
        if os.environ.get("COBRA_PILOT_KEEP_POD", "1") == "1":
            log("KEEP_POD", POD_ID, "set COBRA_PILOT_KEEP_POD=0 to auto-delete on failure")
            raise
        raise
    finally:
        keep = os.environ.get("COBRA_PILOT_KEEP_POD", "1") == "1"
        success_marker = OUT / "remote" / "pilot-out" / "RUN.json"
        should_delete = (not keep) or success_marker.is_file()
        if not should_delete:
            log("skip_terminate_pending_retry", POD_ID)
        else:
            ended = datetime.now(UTC)
            hours = (ended - started).total_seconds() / 3600.0
            est = round(hours * float(cost or 0), 4)
            dst, _ = api("DELETE", f"https://rest.runpod.io/v1/pods/{POD_ID}")
            time.sleep(3)
            st2, pods2 = api("GET", "https://rest.runpod.io/v1/pods")
            remain = []
            if isinstance(pods2, list):
                remain = [p.get("id") for p in pods2 if p.get("id") == POD_ID]
            cost_rec = {
                "schema": "cobra.cloud.cost_record.v1",
                "phase": "4.2-pilot",
                "status": "terminated" if dst in (200, 204) else f"delete_{dst}",
                "provider": "RunPod",
                "pod_id": POD_ID,
                "gpu": gpu,
                "hourly_rate_at_launch_usd": cost,
                "launch_timestamp": started.isoformat(),
                "termination_timestamp": ended.isoformat(),
                "billed_or_estimated_duration_hours": round(hours, 4),
                "estimated_compute_cost_usd": est,
                "approved_spending_ceiling_usd": 10.0,
                "delete_http_status": dst,
                "remaining_matching_pod_ids": remain,
            }
            (OUT / "cost-record.json").write_text(
                json.dumps(cost_rec, indent=2) + "\n", encoding="utf-8"
            )
            (CLOUD / "phase42-cost-record.json").write_text(
                json.dumps(cost_rec, indent=2) + "\n", encoding="utf-8"
            )
            log("terminated", dst, "cost_usd", est, "hours", round(hours, 4))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
