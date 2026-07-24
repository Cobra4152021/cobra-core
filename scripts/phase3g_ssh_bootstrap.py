#!/usr/bin/env python3
"""Phase 3G: ensure PUBLIC_KEY on a RunPod pod and verify SSH (no secrets printed)."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def log(*args: object) -> None:
    print(*args, flush=True)


def api(method: str, url: str, data: dict | None = None):
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("RUNPOD_API_KEY missing")
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
        return resp.status, json.loads(raw.decode()) if raw else {}


def tcp_ok(ip: str, port: int) -> bool:
    s = socket.socket()
    s.settimeout(4)
    try:
        s.connect((ip, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def load_pubkeys() -> str:
    pubs: list[str] = []
    for path in (
        Path.home() / ".runpod" / "ssh" / "runpodctl-ssh-key.pub",
        Path.home() / ".ssh" / "id_ed25519.pub",
    ):
        if path.is_file():
            pubs.append(path.read_text(encoding="utf-8").strip())
    if not pubs:
        raise RuntimeError("no local public keys found")
    return "\n".join(pubs) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pod-id", required=True)
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Stop/start pod after setting PUBLIC_KEY (needed if authorized_keys stale)",
    )
    parser.add_argument("--skip-patch", action="store_true")
    args = parser.parse_args()

    log("credential_present", True)
    pod = args.pod_id
    combined = load_pubkeys()

    if not args.skip_patch:
        st, p = api(
            "PATCH",
            f"https://rest.runpod.io/v1/pods/{pod}",
            {"env": {"PUBLIC_KEY": combined, "SSH_PUBLIC_KEY": combined}},
        )
        env = p.get("env") or {}
        log("patch", st, "has_PUBLIC_KEY", "PUBLIC_KEY" in env)

    if args.restart:
        log("stop", api("POST", f"https://rest.runpod.io/v1/pods/{pod}/stop")[0])
        for _i in range(40):
            _, p = api("GET", f"https://rest.runpod.io/v1/pods/{pod}")
            if str(p.get("desiredStatus", "")).upper() in {"EXITED", "STOPPED"}:
                break
            time.sleep(2)
        log("start", api("POST", f"https://rest.runpod.io/v1/pods/{pod}/start")[0])

    ip = None
    port = 0
    for i in range(60):
        _, p = api("GET", f"https://rest.runpod.io/v1/pods/{pod}")
        ip = p.get("publicIp")
        port = int((p.get("portMappings") or {}).get("22") or 0)
        st = p.get("desiredStatus")
        tcp = "OK" if ip and port and tcp_ok(ip, port) else "WAIT"
        log(f"wait[{i}] status={st} port={port} tcp={tcp}")
        if str(st).upper() == "RUNNING" and tcp == "OK":
            break
        time.sleep(5)

    if not ip or not port:
        log("RESULT SSH_FAILED no_endpoint")
        return 3

    common = [
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
        "ConnectTimeout=20",
        "-o",
        "NumberOfPasswordPrompts=0",
    ]
    for label, keypath in (
        ("runpodctl", Path.home() / ".runpod" / "ssh" / "runpodctl-ssh-key"),
        ("ed25519", Path.home() / ".ssh" / "id_ed25519"),
    ):
        if not keypath.is_file():
            continue
        cmd = [
            "ssh",
            *common,
            "-i",
            str(keypath),
            "-p",
            str(port),
            f"root@{ip}",
            "echo SSH_OK; nvidia-smi -L; uname -n",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log(label, "exit", r.returncode)
        if r.returncode == 0:
            log((r.stdout or "").replace(ip, "<IP>")[:800])
            (ROOT / "evaluations/cloud/.ssh-method.local.json").write_text(
                json.dumps(
                    {"pod_id": pod, "label": label, "port": port, "public_ip_present": True},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            log("RESULT SSH_OK")
            return 0
    log("RESULT SSH_FAILED")
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
