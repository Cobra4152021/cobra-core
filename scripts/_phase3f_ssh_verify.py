#!/usr/bin/env python3
"""Verify SSH to adopted pod without mutating it (no secrets printed)."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import urllib.request
from pathlib import Path

POD = "txw75nv9hn96hu"
ROOT = Path(__file__).resolve().parents[1]


def log(*args: object) -> None:
    print(*args, flush=True)


def get_pod() -> dict:
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    req = urllib.request.Request(
        "https://rest.runpod.io/v1/pods",
        headers={"Authorization": f"Bearer {key}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        pods = json.loads(resp.read().decode())
    matches = [p for p in pods if p.get("id") == POD]
    if not matches:
        raise RuntimeError("pod_missing")
    return matches[0]


def main() -> int:
    p = get_pod()
    ip = p.get("publicIp")
    port = int((p.get("portMappings") or {}).get("22") or 0)
    env = p.get("env") or {}
    log("status", p.get("desiredStatus"), "port", port, "ip_present", bool(ip))
    log("env_has_PUBLIC_KEY", "PUBLIC_KEY" in env)
    log("env_has_SSH_PUBLIC_KEY", "SSH_PUBLIC_KEY" in env)
    if not ip or not port:
        log("RESULT SSH_FAILED missing_endpoint")
        return 3
    s = socket.socket()
    s.settimeout(5)
    try:
        s.connect((ip, port))
        log("tcp OK")
    except OSError as e:
        log("tcp", type(e).__name__)
        log("RESULT SSH_FAILED tcp")
        return 3
    finally:
        s.close()

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
        "KbdInteractiveAuthentication=no",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=20",
        "-o",
        "NumberOfPasswordPrompts=0",
    ]
    keys = [
        ("runpodctl", str(Path.home() / ".runpod" / "ssh" / "runpodctl-ssh-key")),
        ("ed25519", str(Path.home() / ".ssh" / "id_ed25519")),
    ]
    for label, keypath in keys:
        cmd = [
            "ssh",
            *common,
            "-vv",
            "-i",
            keypath,
            "-p",
            str(port),
            f"root@{ip}",
            "echo SSH_OK; nvidia-smi -L; whoami",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        # redact IP from stderr; keep only auth-relevant lines
        err_lines = []
        for line in (r.stderr or "").splitlines():
            low = line.lower()
            if any(
                x in low
                for x in (
                    "offering",
                    "authentications",
                    "publickey",
                    "permission denied",
                    "accepted",
                    "try",
                    "server accepts",
                    "we did not",
                )
            ):
                err_lines.append(line.replace(ip, "<IP>")[-220:])
        log(label, "exit", r.returncode)
        for line in err_lines[-12:]:
            log(" ", line)
        if r.returncode == 0:
            log((r.stdout or "").replace(ip, "<IP>")[:1000])
            (ROOT / "evaluations/cloud/.ssh-ok.local").write_text(label + "\n", encoding="utf-8")
            (ROOT / "evaluations/cloud/.ssh-method.local.json").write_text(
                json.dumps({"label": label, "port": port, "pod_id": POD}, indent=2) + "\n",
                encoding="utf-8",
            )
            log("RESULT SSH_OK")
            return 0
    log("RESULT SSH_FAILED")
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
