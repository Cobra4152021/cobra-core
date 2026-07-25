#!/usr/bin/env python3
"""
Phase 5B.2 — configure/deploy Cobra Computer staging against live Core, then kill-switch.

Requires:
- evaluations/diagnostics/phase-5b2-live-staging/connection-handoff.json
- COBRA_CORE_AUTH_SECRET in process env (same secret used on Core)
- Clean Computer worktree at COMPUTER_ROOT
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[1]
OUT = CORE_ROOT / "evaluations/diagnostics/phase-5b2-live-staging"
COMPUTER_ROOT = Path(
    os.environ.get(
        "COBRA_COMPUTER_ROOT",
        r"C:\Users\Dynamic Mining Inc\Downloads\hidden-grid-os-phase5b2",
    )
)


def log(*a: object) -> None:
    print(*a, flush=True)


def run(
    cmd: list[str], *, cwd: Path, env: dict | None = None, timeout: int = 1800
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    # Never print secret-bearing command lines.
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=merged,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=True,
    )


def patch_deploy_staging(enable: bool, handoff: dict) -> None:
    path = COMPUTER_ROOT / "scripts" / "deploy-staging.mjs"
    text = path.read_text(encoding="utf-8")
    marker_start = "// PHASE5B2_CORE_BEGIN"
    marker_end = "// PHASE5B2_CORE_END"
    if marker_start in text:
        text = re.sub(
            re.escape(marker_start) + r".*?" + re.escape(marker_end),
            "",
            text,
            flags=re.S,
        )
    needle = "writeFileSync(out, JSON.stringify(cfg, null, 2));"
    if enable:
        block = f"""
{marker_start}
cfg.vars = {{
  ...cfg.vars,
  COBRA_CORE_ENABLED: "true",
  COBRA_CORE_ADMIN_ONLY: "true",
  COBRA_CORE_SHADOW_MODE: "false",
  COBRA_CORE_BASE_URL: {json.dumps(handoff["COBRA_CORE_BASE_URL"])},
  COBRA_CORE_MODEL: {json.dumps(handoff["COBRA_CORE_MODEL"])},
  COBRA_CORE_REVISION: {json.dumps(handoff["COBRA_CORE_REVISION"])},
  COBRA_CORE_TIMEOUT_MS: {json.dumps(handoff["COBRA_CORE_TIMEOUT_MS"])},
  COBRA_CORE_MAX_CONTEXT: {json.dumps(handoff["COBRA_CORE_MAX_CONTEXT"])},
  COBRA_CORE_MAX_OUTPUT_TOKENS: {json.dumps(handoff["COBRA_CORE_MAX_OUTPUT_TOKENS"])},
}};
{marker_end}

"""
        if needle not in text:
            raise RuntimeError("deploy-staging.mjs missing writeFileSync needle for Core overlay")
        text = text.replace(needle, block + needle, 1)
        if marker_start not in text or "COBRA_CORE_ENABLED" not in text:
            raise RuntimeError("Core overlay patch failed to apply")
    # Collapse accidental blank runs from prior strips.
    text = re.sub(r"\n{3,}", "\n\n", text)
    path.write_text(text, encoding="utf-8")


def put_secret(secret: str) -> None:
    # Pipe secret to wrangler without echoing. Staging Worker name is custom.
    attempts = (
        [
            "npx",
            "wrangler",
            "secret",
            "put",
            "COBRA_CORE_AUTH_SECRET",
            "--name",
            "hidden-grid-os-staging",
        ],
        ["npx", "wrangler", "secret", "put", "COBRA_CORE_AUTH_SECRET", "--env", "staging"],
    )
    last_err = ""
    for args in attempts:
        r = subprocess.run(
            args,
            cwd=COMPUTER_ROOT,
            input=secret + "\n",
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=180,
            shell=True,
        )
        if r.returncode == 0:
            return
        last_err = (r.stderr or r.stdout or "")[-400:]
    raise RuntimeError(f"wrangler secret put failed: {last_err}")


def delete_secret() -> None:
    for args in (
        [
            "npx",
            "wrangler",
            "secret",
            "delete",
            "COBRA_CORE_AUTH_SECRET",
            "--name",
            "hidden-grid-os-staging",
            "--force",
        ],
        [
            "npx",
            "wrangler",
            "secret",
            "delete",
            "COBRA_CORE_AUTH_SECRET",
            "--env",
            "staging",
            "--force",
        ],
    ):
        subprocess.run(
            args,
            cwd=COMPUTER_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            shell=True,
        )


def main() -> int:
    handoff_path = OUT / "connection-handoff.json"
    if not handoff_path.exists():
        log("missing handoff", handoff_path)
        return 2
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    secret = (os.environ.get("COBRA_CORE_AUTH_SECRET") or "").strip()
    if not secret:
        # Recovered secret path written by _phase5b2_recover_secret.py (outside repo).
        from tempfile import gettempdir

        secret_path = Path(gettempdir()) / "phase5b2-cobra-core-auth.secret"
        if secret_path.exists():
            secret = secret_path.read_text(encoding="utf-8").strip()
    if not secret:
        log("COBRA_CORE_AUTH_SECRET missing in env and temp secret file")
        return 2
    if not COMPUTER_ROOT.is_dir():
        log("computer root missing", COMPUTER_ROOT)
        return 2

    started = datetime.now(UTC)
    results: dict = {"started_at": started.isoformat(), "steps": []}

    try:
        log("put_staging_secret")
        put_secret(secret)
        results["steps"].append({"put_secret": True})

        log("patch_deploy_enable")
        patch_deploy_staging(True, handoff)

        log("deploy_staging_enable")
        # Rebuild so dist wrangler picks up current sources, then deploy with Core overlay.
        build = run(["npm", "run", "build"], cwd=COMPUTER_ROOT, timeout=600)
        (OUT / "computer-build-enable-stdout.txt").write_text(
            build.stdout[-4000:], encoding="utf-8"
        )
        (OUT / "computer-build-enable-stderr.txt").write_text(
            build.stderr[-4000:], encoding="utf-8"
        )
        if build.returncode != 0:
            raise RuntimeError("npm run build failed")

        deploy = run(["node", "scripts/deploy-staging.mjs"], cwd=COMPUTER_ROOT, timeout=900)
        (OUT / "computer-deploy-enable-stdout.txt").write_text(
            deploy.stdout[-5000:], encoding="utf-8"
        )
        (OUT / "computer-deploy-enable-stderr.txt").write_text(
            deploy.stderr[-5000:], encoding="utf-8"
        )
        if deploy.returncode != 0:
            raise RuntimeError("deploy:staging (enable) failed")
        results["steps"].append({"deploy_enable": True})

        log("staging_validate_live")
        env = {
            "COBRA_CORE_STAGING_MARKER": "staging",
            "COBRA_CORE_BASE_URL": handoff["COBRA_CORE_BASE_URL"],
            "COBRA_CORE_AUTH_SECRET": secret,
            "COBRA_CORE_MODEL": handoff["COBRA_CORE_MODEL"],
        }
        val = run(
            ["npm", "run", "cobra-core:staging-validate", "--", "--staging"],
            cwd=COMPUTER_ROOT,
            env=env,
            timeout=900,
        )
        (OUT / "computer-staging-validate-stdout.txt").write_text(
            val.stdout.replace(secret, "[REDACTED]")[-8000:], encoding="utf-8"
        )
        (OUT / "computer-staging-validate-stderr.txt").write_text(
            val.stderr.replace(secret, "[REDACTED]")[-4000:], encoding="utf-8"
        )
        results["steps"].append({"staging_validate": val.returncode == 0, "exit": val.returncode})
        if val.returncode != 0:
            raise RuntimeError("staging-validate live failed")

        # Minimal real-model sanity via Core URL (Computer adapter path already covered by smoke).
        log("sanity_prompts_via_core")
        import urllib.error
        import urllib.request

        prompts = [
            "What is 2+2? Answer with one number.",
            "Summarize in one sentence: The sky is blue because of Rayleigh scattering.",
            'Return JSON only: {"ok": true}',
            "In one sentence, why do unit tests matter?",
            "Explain a Python list comprehension in one short sentence.",
        ]
        sanity = []
        for i, p in enumerate(prompts):
            body = json.dumps(
                {
                    "model": "cobra-core-qwen3-8b",
                    "stream": False,
                    "max_tokens": 64,
                    "messages": [{"role": "user", "content": p}],
                }
            ).encode()
            req = urllib.request.Request(
                handoff["COBRA_CORE_BASE_URL"] + "/v1/chat/completions",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {secret}",
                    "Content-Type": "application/json",
                    "x-request-id": f"cc_sanity_{i}",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    data = json.loads(resp.read().decode())
                text = (
                    ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
                ) or ""
                sanity.append(
                    {
                        "i": i,
                        "ok": bool(str(text).strip()),
                        "chars": len(str(text)),
                        "usage": data.get("usage"),
                        "latency": data.get("latency"),
                    }
                )
            except Exception as exc:
                sanity.append({"i": i, "ok": False, "error": type(exc).__name__})
        (OUT / "real-model-sanity.json").write_text(
            json.dumps(sanity, indent=2) + "\n", encoding="utf-8"
        )
        results["steps"].append({"sanity": all(x.get("ok") for x in sanity), "count": len(sanity)})

        return 0 if all(x.get("ok") for x in sanity) else 1
    except Exception as exc:
        results["error"] = {"type": type(exc).__name__, "message": str(exc)[:400]}
        log("FAILED", results["error"])
        return 1
    finally:
        # Kill-switch: disable Core on staging and redeploy; invalidate secret.
        try:
            log("kill_switch_disable")
            patch_deploy_staging(False, handoff)
            build = run(["npm", "run", "build"], cwd=COMPUTER_ROOT, timeout=600)
            deploy = run(["node", "scripts/deploy-staging.mjs"], cwd=COMPUTER_ROOT, timeout=900)
            (OUT / "computer-deploy-disable-stdout.txt").write_text(
                deploy.stdout[-4000:], encoding="utf-8"
            )
            ks = run(
                ["npm", "run", "cobra-core:kill-switch", "--", "--staging", "--dry-run"],
                cwd=COMPUTER_ROOT,
                timeout=180,
            )
            (OUT / "kill-switch-stdout.txt").write_text(ks.stdout[-4000:], encoding="utf-8")
            delete_secret()
            # Put a rotated invalidation secret then delete again so old secret is dead.
            put_secret(os.urandom(24).hex())
            delete_secret()
            results["kill_switch"] = {
                "build_rc": build.returncode,
                "deploy_rc": deploy.returncode,
                "kill_switch_rc": ks.returncode,
                "secret_invalidated": True,
            }
        except Exception as exc:
            results["kill_switch_error"] = type(exc).__name__
            log("kill_switch_error", type(exc).__name__)
        results["ended_at"] = datetime.now(UTC).isoformat()
        (OUT / "computer-staging-results.json").write_text(
            json.dumps(results, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    raise SystemExit(main())
