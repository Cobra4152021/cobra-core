#!/usr/bin/env python3
"""Run Protocol V1 direct validation against HTTPS base URL from the GPU pod."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

SSH_KEY = Path.home() / ".runpod/ssh/runpodctl-ssh-key"
OUT = Path(__file__).resolve().parents[1] / "evaluations/diagnostics/phase-5b2-live-staging"


def remote(
    ip: str, port: int, script: str, timeout: int = 900
) -> subprocess.CompletedProcess[bytes]:
    b64 = base64.b64encode(script.encode()).decode()
    return subprocess.run(
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
            f"echo {b64} | base64 -d | bash -s",
        ],
        capture_output=True,
        timeout=timeout,
    )


REMOTE_PY = r"""
import json, os, socket, time, urllib.request, urllib.error
from urllib.parse import urlparse

token=os.environ["TOKEN"]
base_https=os.environ["BASE"].rstrip("/")
rev=os.environ["REV"]
sha=os.environ["SHA"]
results=[]

def check(name, ok, detail=""):
    results.append({"name":name,"pass":bool(ok),"detail":str(detail)[:200]})
    print(("PASS" if ok else "FAIL"), name, str(detail)[:120])

def req(base, method, path, token=None, body=None, rid=None, timeout=300):
    data=None if body is None else json.dumps(body).encode()
    headers={"Accept":"application/json","Content-Type":"application/json"}
    if token is not None:
        headers["Authorization"]=f"Bearer {token}"
    if rid:
        headers["x-request-id"]=rid
    r=urllib.request.Request(base+path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode()), dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors="replace")
        try: payload=json.loads(raw)
        except Exception: payload={"raw":raw[:200]}
        return e.code, payload, dict(e.headers)

# Phase A — loopback Protocol V1 conformance (authoritative for frozen contract).
base_local="http://127.0.0.1:18080"
st,body,hdrs=req(base_local,"GET","/health",token=token,rid="cc_5b2_health")
check("health_auth_ok", st==200 and body.get("protocolVersion")=="1" and body.get("compatibilityVersion")=="1" and body.get("model")=="cobra-core-qwen3-8b" and body.get("reason")=="ok", f"status={st} reason={body.get('reason')}")
check("revision", body.get("revision")==rev, body.get("revision"))
check("gitSha", str(body.get("gitSha","")).startswith(sha[:12]), body.get("gitSha"))
limits=body.get("limits") or {}
check("limits_context", limits.get("maxContext")==8192, limits)
check("limits_output", limits.get("maxOutputTokens")==256, limits)
st,body,_=req(base_local,"GET","/health",token=None)
check("health_no_auth", st==401, st)
st,body,_=req(base_local,"GET","/health",token="definitely-wrong")
check("health_bad_auth", st==401, st)
rid="cc_5b2_complete"
st,body,hdrs=req(base_local,"POST","/v1/chat/completions",token=token,rid=rid,body={"model":"cobra-core-qwen3-8b","stream":False,"max_tokens":48,"messages":[{"role":"user","content":"Reply with exactly: pong"}]},timeout=300)
text=((((body.get("choices") or [{}])[0].get("message") or {}).get("content")) or "")
usage=body.get("usage") or {}
latency=body.get("latency") or {}
check("completion_ok", st==200 and bool(str(text).strip()), f"status={st} len={len(str(text))}")
check("request_id_preserved", hdrs.get("x-request-id")==rid or body.get("requestId")==rid, "")
check("usage", all(k in usage for k in ("prompt_tokens","completion_tokens","total_tokens")) and usage.get("total_tokens")==usage.get("prompt_tokens",-1)+usage.get("completion_tokens",-1), usage)
check("latency", all(k in latency for k in ("queue_ms","provider_latency_ms","inference_ms","total_ms")), latency)
check("no_traceback", "traceback" not in json.dumps(body).lower(), "")
st,body,hdrs=req(base_local,"POST","/v1/chat/completions",token=token,body={"model":"cobra-core-qwen3-8b","stream":False,"max_tokens":16,"messages":[{"role":"user","content":"id"}]})
gen=hdrs.get("x-request-id") or body.get("requestId") or ""
check("request_id_generated", st==200 and str(gen).startswith("cc_"), str(gen)[:40])
st,body,_=req(base_local,"POST","/v1/chat/completions",token=token,body={"model":"cobra-core-qwen3-8b","stream":False,"max_tokens":99999,"messages":[{"role":"user","content":"Say hi in under five words."}]},timeout=300)
check("output_limit_cap", st==200 and bool(body.get("choices")), st)
st,body,_=req(base_local,"POST","/v1/chat/completions",token=token,body={"model":"cobra-core-qwen3-8b","stream":False,"max_tokens":8,"messages":[]})
check("bad_request", st==400 and body.get("code")=="bad_request", st)
check("safe_error", "traceback" not in json.dumps(body).lower(), "")

# Phase B — HTTPS tunnel reachability with DNS retries (required for Computer staging).
host=urlparse(base_https).hostname or ""
dns_ok=False
for i in range(30):
    try:
        socket.getaddrinfo(host, 443)
        dns_ok=True
        break
    except Exception as e:
        print("tunnel_dns_wait", i, type(e).__name__)
        time.sleep(2)
check("tunnel_dns", dns_ok, host)
https_ok=False
https_detail=""
if dns_ok:
    for i in range(10):
        try:
            st,body,_=req(base_https,"GET","/health",token=token,timeout=60)
            https_ok = st==200 and body.get("reason")=="ok"
            https_detail=f"status={st} reason={body.get('reason')}"
            if https_ok:
                break
        except Exception as e:
            https_detail=f"{type(e).__name__}:{str(e)[:80]}"
            time.sleep(2)
check("tunnel_https_health", https_ok, https_detail)

open("/workspace/logs/direct-results.json","w").write(json.dumps(results, indent=2))
print("RESULTS_JSON_OK")
"""


def validate(
    ip: str,
    port: int,
    base: str,
    token: str,
    revision: str,
    git_sha: str,
) -> list[dict]:
    secret_b64 = base64.b64encode(token.encode()).decode()
    base_b64 = base64.b64encode(base.encode()).decode()
    local_py = OUT / "_remote_direct_validate.py"
    OUT.mkdir(parents=True, exist_ok=True)
    local_py.write_text(REMOTE_PY, encoding="utf-8")
    scp = subprocess.run(
        [
            "scp",
            "-i",
            str(SSH_KEY),
            "-P",
            str(port),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            str(local_py),
            f"root@{ip}:/workspace/logs/_remote_direct_validate.py",
        ],
        capture_output=True,
        timeout=60,
    )
    if scp.returncode != 0:
        return [{"name": "scp_validator", "pass": False, "detail": scp.stderr.decode()[-200:]}]

    script = f"""
set -euo pipefail
export TOKEN="$(echo {secret_b64} | base64 -d)"
export BASE="$(echo {base_b64} | base64 -d)"
export REV="{revision}"
export SHA="{git_sha}"
python3 /workspace/logs/_remote_direct_validate.py
"""
    r = remote(ip, port, script, timeout=900)
    (OUT / "direct-validate-stdout.txt").write_bytes((r.stdout or b"")[-8000:])
    (OUT / "direct-validate-stderr.txt").write_bytes(r.stderr or b"")
    pull = subprocess.run(
        [
            "scp",
            "-i",
            str(SSH_KEY),
            "-P",
            str(port),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            f"root@{ip}:/workspace/logs/direct-results.json",
            str(OUT / "direct-core-results-raw.json"),
        ],
        capture_output=True,
        timeout=60,
    )
    if pull.returncode == 0 and (OUT / "direct-core-results-raw.json").exists():
        return json.loads((OUT / "direct-core-results-raw.json").read_text(encoding="utf-8"))
    return [{"name": "direct_validate_pull", "pass": False, "detail": f"rc={r.returncode}"}]
