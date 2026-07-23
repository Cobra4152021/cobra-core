#!/usr/bin/env python3
"""Phase 3F Gate 4+ runner: transfer, verify, qualify on adopted RunPod pod.

Never prints secrets. Does not create pods. Does not run CobraBench.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POD = "txw75nv9hn96hu"
REQUIRED_COMMIT = "695ea8833229b183e5792c49e3888ec4dde9e5f2"
BUNDLE = ROOT / "artifacts/cloud-qwen3-runtime-qualification/cobra-core-phase3e.bundle"
BUNDLE_SHA = "a50eee0232ee35cccf55fa69fdde4fd7aacdab5b0d6919f113cf4a199b44ba89"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
LOCAL_MODEL = Path(f"D:/cobra-models/qwen/qwen3-8b/{MODEL_REV}/artifacts")
# Use /workspace (pod network volume). Overlay / is only ~30GB and cannot hold model+venv.
REMOTE_HOME = "/workspace"
REMOTE_REPO = f"{REMOTE_HOME}/cobra-core-cloud"
REMOTE_MODEL = f"{REMOTE_HOME}/models/qwen3-8b"
REMOTE_DIAG = f"{REMOTE_REPO}/evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification"
REMOTE_TRANSFER = f"{REMOTE_HOME}/transfer"
SSH_KEY = Path.home() / ".runpod" / "ssh" / "runpodctl-ssh-key"


def log(*args: object) -> None:
    print(*args, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def get_pod() -> dict:
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("RUNPOD_API_KEY missing")
    req = urllib.request.Request(
        "https://rest.runpod.io/v1/pods",
        headers={"Authorization": f"Bearer {key}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        pods = json.loads(resp.read().decode())
    matches = [p for p in pods if p.get("id") == POD]
    if not matches:
        raise RuntimeError("adopted pod not found; refusing to create another")
    if len([p for p in pods if str(p.get("desiredStatus", "")).upper() == "RUNNING"]) > 1:
        raise RuntimeError("more than one RUNNING pod; stop")
    return matches[0]


def ssh_base(ip: str, port: int) -> list[str]:
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "PreferredAuthentications=publickey",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=30",
        "-i",
        str(SSH_KEY),
        "-p",
        str(port),
        f"root@{ip}",
    ]


def scp_base(ip: str, port: int) -> list[str]:
    return [
        "scp",
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "PreferredAuthentications=publickey",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=30",
        "-i",
        str(SSH_KEY),
        "-P",
        str(port),
    ]


def run(cmd: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def ssh(
    ip: str, port: int, remote_cmd: str, *, timeout: int | None = 120
) -> subprocess.CompletedProcess[str]:
    # Avoid Windows CRLF breaking remote bash -c scripts.
    normalized = remote_cmd.replace("\r\n", "\n").replace("\r", "\n")
    return run([*ssh_base(ip, port), normalized], timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=["probe", "bundle", "model", "env", "qualify", "export", "all"],
        default="probe",
    )
    args = parser.parse_args()

    p = get_pod()
    ip = p.get("publicIp")
    port = int((p.get("portMappings") or {}).get("22") or 0)
    cost = p.get("costPerHr")
    log(
        "pod",
        POD,
        "status",
        p.get("desiredStatus"),
        "cost_per_hr",
        cost,
        "port",
        port,
        "ip_present",
        bool(ip),
        "create_new_pod",
        False,
    )
    if not ip or not port:
        log("missing SSH endpoint")
        return 2

    r = ssh(ip, port, "echo SSH_OK; nvidia-smi -L; uname -a; python3 --version")
    log("ssh_probe exit", r.returncode)
    if r.returncode != 0:
        log((r.stderr or "")[-400:])
        return 4
    log((r.stdout or "").replace(ip, "<IP>")[:800])

    if args.stage == "probe":
        return 0

    if args.stage in {"bundle", "all"}:
        if not BUNDLE.is_file():
            log("missing bundle")
            return 2
        digest = sha256_file(BUNDLE)
        log("bundle_sha_local", digest)
        if digest != BUNDLE_SHA:
            log("bundle hash mismatch")
            return 2
        # prepare remote dirs and transfer bundle
        ssh(ip, port, f"mkdir -p {REMOTE_TRANSFER} {REMOTE_HOME}/models")
        log("scp bundle begin")
        t0 = time.time()
        c = run(
            [
                *scp_base(ip, port),
                str(BUNDLE),
                f"root@{ip}:{REMOTE_TRANSFER}/cobra-core-phase3e.bundle",
            ],
            timeout=600,
        )
        log("scp bundle exit", c.returncode, "seconds", round(time.time() - t0, 1))
        if c.returncode != 0:
            log((c.stderr or "")[-400:])
            return 5
        restore = f"""
set -euo pipefail
BUNDLE={REMOTE_TRANSFER}/cobra-core-phase3e.bundle
EXPECTED={BUNDLE_SHA}
got=$(sha256sum "$BUNDLE" | awk '{{print $1}}')
echo bundle_sha_remote=$got
test "$got" = "$EXPECTED"
rm -rf {REMOTE_REPO}
git clone "$BUNDLE" {REMOTE_REPO}
cd {REMOTE_REPO}
git checkout {REQUIRED_COMMIT}
test "$(git rev-parse HEAD)" = "{REQUIRED_COMMIT}"
test -z "$(git status --short)"
echo REPO_OK $(git rev-parse HEAD)
df -h / /workspace
"""
        r = ssh(ip, port, restore, timeout=180)
        log("restore exit", r.returncode)
        log((r.stdout or "")[-600:])
        if r.returncode != 0:
            log((r.stderr or "")[-600:])
            return 5

    if args.stage in {"model", "all"}:
        if not LOCAL_MODEL.is_dir():
            log("missing local model artifacts")
            return 2
        inv = json.loads(
            (ROOT / "evaluations/model-inventory/qwen3-8b-local-inventory.json").read_text(
                encoding="utf-8"
            )
        )
        if inv.get("inventory_hash") != MODEL_INV:
            log("local inventory hash mismatch")
            return 2
        # Transfer inventory + integrity first, then weight files via tar stream
        ssh(ip, port, f"mkdir -p {REMOTE_MODEL}")
        inv_paths = [
            ROOT / "evaluations/model-inventory/qwen3-8b-local-inventory.json",
            ROOT / "evaluations/model-inventory/qwen3-8b-file-integrity.json",
            ROOT / "artifacts/cloud-qwen3-runtime-qualification/model-inventory.json",
            ROOT / "artifacts/cloud-qwen3-runtime-qualification/model-file-integrity.json",
        ]
        for path in inv_paths:
            c = run(
                [*scp_base(ip, port), str(path), f"root@{ip}:{REMOTE_TRANSFER}/{path.name}"],
                timeout=120,
            )
            if c.returncode != 0:
                log("scp meta failed", path.name, (c.stderr or "")[-200:])
                return 5
        # Size precheck against inventory; re-transfer if incomplete/corrupt.
        pack = json.loads(
            (ROOT / "artifacts/cloud-qwen3-runtime-qualification/model-inventory.json").read_text(
                encoding="utf-8"
            )
        )
        expected_bytes = sum(int(x["size_bytes"]) for x in pack["weight_file_inventory"])
        pre = ssh(
            ip,
            port,
            "python3 - <<'PY'\n"
            "from pathlib import Path\n"
            f"root=Path('{REMOTE_MODEL}')\n"
            f"expected={expected_bytes}\n"
            "weights=["
            + ",".join(repr(x["relpath"]) for x in pack["weight_file_inventory"])
            + "]\n"
            "sizes={}\n"
            "if root.is_dir():\n"
            "  for n in weights:\n"
            "    p=root/n\n"
            "    sizes[n]=p.stat().st_size if p.is_file() else 0\n"
            "ok=bool(sizes) and all(sizes.get(n,0)>0 for n in weights) and sum(sizes.values())==expected\n"
            "print('PRECHECK', 'OK' if ok else 'NEED_TRANSFER')\n"
            "print('weight_bytes', sum(sizes.values()) if sizes else 0, 'expected', expected)\n"
            "PY",
            timeout=60,
        )
        log((pre.stdout or "").strip())
        if "PRECHECK OK" not in (pre.stdout or ""):
            log("clearing incomplete remote model")
            ssh(ip, port, f"rm -rf {REMOTE_MODEL} && mkdir -p {REMOTE_MODEL}", timeout=120)
            log("model tar stream begin")
            t0 = time.time()
            tar_cmd = ["tar", "-C", str(LOCAL_MODEL), "-cf", "-", "."]
            ssh_cmd = [
                *ssh_base(ip, port),
                f"mkdir -p {REMOTE_MODEL} && tar -C {REMOTE_MODEL} -xf - && echo TAR_EXTRACT_OK",
            ]
            with (
                subprocess.Popen(tar_cmd, stdout=subprocess.PIPE) as src,
                subprocess.Popen(
                    ssh_cmd, stdin=src.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                ) as dst,
            ):
                assert src.stdout is not None
                src.stdout.close()
                _out, err = dst.communicate(timeout=7200)
                code = dst.returncode
            log("model tar stream exit", code, "seconds", round(time.time() - t0, 1))
            if _out:
                log(_out.decode("utf-8", "replace")[-200:])
            if code != 0:
                log((err or b"").decode("utf-8", "replace")[-400:])
                return 5
        else:
            log("model sizes match inventory; verifying hashes")
        verify = f"""
set -euo pipefail
cd {REMOTE_MODEL}
python3 - <<'PY'
import hashlib, json
from pathlib import Path
root = Path("{REMOTE_MODEL}")
inv_path = Path("{REMOTE_TRANSFER}/qwen3-8b-local-inventory.json")
inv = json.loads(inv_path.read_text())
assert inv["inventory_hash"] == "{MODEL_INV}"
assert inv["model_revision"] == "{MODEL_REV}"
# verify weight shards listed in transfer package inventory
pack = json.loads(Path("{REMOTE_TRANSFER}/model-inventory.json").read_text())
for item in pack["weight_file_inventory"]:
    p = root / item["relpath"]
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""):
            h.update(chunk)
    digest = h.hexdigest()
    assert digest == item["sha256"], (item["relpath"], digest)
    assert p.stat().st_size == item["size_bytes"]
    print("ok", item["relpath"])
print("MODEL_OK", inv["inventory_hash"])
PY
"""
        r = ssh(ip, port, verify, timeout=1800)
        log("model verify exit", r.returncode)
        log((r.stdout or "")[-800:])
        if r.returncode != 0:
            log((r.stderr or "")[-800:])
            return 5

    if args.stage in {"env", "all"}:
        # Upload cloud lock + creation helpers that may post-date the bundle commit
        for rel in [
            "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-lock.txt",
            "evaluations/environments/cloud-qwen3-runtime/creation-commands.md",
            "scripts/qualify_qwen3_8b_cloud.py",
            "scripts/_phase3f_linux_qualify_worker.py",
            "scripts/_phase3f_linux_qualify_parent.py",
            "evaluations/cloud/authorization-record.json",
        ]:
            local = ROOT / rel
            if not local.is_file():
                log("missing local helper", rel)
                continue
            remote = f"{REMOTE_REPO}/{rel}"
            ssh(ip, port, f"mkdir -p $(dirname {remote})")
            c = run([*scp_base(ip, port), str(local), f"root@{ip}:{remote}"], timeout=120)
            if c.returncode != 0:
                log("scp helper failed", rel, (c.stderr or "")[-200:])
                return 5
        setup = f"""
set -euo pipefail
cd {REMOTE_REPO}
python3 --version
# Prefer 3.11/3.12 if present
PY=python3
if command -v python3.11 >/dev/null 2>&1; then PY=python3.11; fi
if command -v python3.12 >/dev/null 2>&1; then PY=python3.12; fi
echo USING_PY=$PY
$PY -m venv .venv-qwen-cloud
source .venv-qwen-cloud/bin/activate
python -m pip install --upgrade pip==25.1.1 setuptools==80.9.0 wheel==0.45.1
# Prefer pinned cu124 torch; fall back to existing image torch if wheel unavailable
set +e
python -m pip install torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124
TORCH_RC=$?
set -e
if [ "$TORCH_RC" -ne 0 ]; then
  echo TORCH_PIN_FALLBACK_USING_IMAGE_TORCH
  python - <<'PY'
import torch
print('torch', torch.__version__, 'cuda', torch.version.cuda, 'avail', torch.cuda.is_available())
assert torch.cuda.is_available()
PY
else
  python - <<'PY'
import torch
print('torch', torch.__version__, 'cuda', torch.version.cuda, 'avail', torch.cuda.is_available())
assert torch.cuda.is_available()
PY
fi
python -m pip install -r evaluations/environments/cloud-qwen3-runtime/requirements-cloud-lock.txt
python -m pip check || true
python - <<'PY'
import torch, transformers, accelerate, bitsandbytes, numpy, psutil
print('ENV_OK')
print('torch', torch.__version__)
print('cuda_available', torch.cuda.is_available())
print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
print('transformers', transformers.__version__)
print('accelerate', accelerate.__version__)
print('bitsandbytes', bitsandbytes.__version__)
print('numpy', numpy.__version__)
print('psutil', psutil.__version__)
x = torch.zeros(1, device='cuda')
y = x + 1
print('cuda_micro_op', float(y.item()))
PY
nvidia-smi
"""
        r = ssh(ip, port, setup, timeout=3600)
        log("env setup exit", r.returncode)
        log((r.stdout or "")[-2000:])
        if r.returncode != 0:
            log((r.stderr or "")[-2000:])
            return 6

    if args.stage in {"qualify", "all"}:
        # Ensure worker/parent present
        for rel in [
            "scripts/_phase3f_linux_qualify_worker.py",
            "scripts/_phase3f_linux_qualify_parent.py",
        ]:
            local = ROOT / rel
            remote = f"{REMOTE_REPO}/{rel}"
            ssh(ip, port, f"mkdir -p $(dirname {remote})")
            c = run([*scp_base(ip, port), str(local), f"root@{ip}:{remote}"], timeout=120)
            if c.returncode != 0:
                log("missing qualify script transfer", rel)
                return 5
        cmd = f"""
set -euo pipefail
cd {REMOTE_REPO}
source .venv-qwen-cloud/bin/activate
export COBRA_CLOUD_MODEL_DIR={REMOTE_MODEL}
export COBRA_CLOUD_INVENTORY={REMOTE_TRANSFER}/qwen3-8b-local-inventory.json
python scripts/_phase3f_linux_qualify_parent.py
"""
        r = ssh(ip, port, cmd, timeout=7200)
        log("qualify exit", r.returncode)
        log((r.stdout or "")[-3000:])
        if r.returncode != 0:
            log((r.stderr or "")[-3000:])
            return 7

    if args.stage in {"export", "all"}:
        out_dir = ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification"
        out_dir.mkdir(parents=True, exist_ok=True)
        # pull remote diag tree
        remote_tar = f"{REMOTE_TRANSFER}/cloud-diag.tar"
        ssh(
            ip,
            port,
            f"tar -C {REMOTE_DIAG} -cf {remote_tar} . 2>/dev/null || tar -C {REMOTE_REPO}/evaluations/diagnostics -cf {remote_tar} qwen3-8b-cloud-runtime-qualification",
            timeout=300,
        )
        local_tar = ROOT / "artifacts" / "cloud-diag-export.tar"
        c = run(
            [*scp_base(ip, port), f"root@{ip}:{remote_tar}", str(local_tar)],
            timeout=600,
        )
        log("export scp exit", c.returncode)
        if c.returncode != 0:
            log((c.stderr or "")[-400:])
            return 8
        import tarfile

        with tarfile.open(local_tar, "r") as tf:
            tf.extractall(out_dir)
        log("exported_to", out_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
