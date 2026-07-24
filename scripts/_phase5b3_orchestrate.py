#!/usr/bin/env python3
"""
Phase 5B.3 — provision Core, enable Computer staging, run auth-session proof, cleanup.

Uses Phase 5B.2 GPU deploy path (KEEP), then Computer session harness.
Always terminates GPU and disables staging Core in finally.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[1]
OUT = CORE_ROOT / "evaluations/diagnostics/phase-5b3-authenticated-session"
COMPUTER_ROOT = Path(
    os.environ.get(
        "COBRA_COMPUTER_ROOT",
        r"C:\Users\Dynamic Mining Inc\Downloads\hidden-grid-os-phase5b2",
    )
)
LEGACY_OUT = CORE_ROOT / "evaluations/diagnostics/phase-5b2-live-staging"
SECRET_PATH = Path(tempfile.gettempdir()) / "phase5b3-cobra-core-auth.secret"


def log(*a: object) -> None:
    print(*a, flush=True)


def run(cmd: list[str] | str, *, cwd: Path, env: dict | None = None, timeout: int = 3600) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
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


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    results: dict = {"started_at": started.isoformat(), "steps": []}
    secret = ""
    try:
        # 1) Provision Core GPU (reuse 5B.2 script; KEEP for session tests)
        log("provision_core_gpu")
        env = os.environ.copy()
        env["PHASE5B2_KEEP"] = "1"
        # Clear stale ready marker so KEEP only applies if this run succeeds.
        for stale in ("core-ready.json", "connection-handoff.json", "keep-active.json"):
            p = LEGACY_OUT / stale
            if p.exists():
                p.unlink()
        prov = run(
            [sys.executable, str(CORE_ROOT / "scripts/_phase5b2_live_staging.py")],
            cwd=CORE_ROOT,
            env=env,
            timeout=9000,
        )
        (OUT / "core-provision-stdout.txt").write_text((prov.stdout or "")[-8000:], encoding="utf-8")
        (OUT / "core-provision-stderr.txt").write_text((prov.stderr or "")[-4000:], encoding="utf-8")
        if prov.returncode != 0:
            raise RuntimeError("core provision failed")
        handoff_src = LEGACY_OUT / "connection-handoff.json"
        if not handoff_src.exists():
            raise RuntimeError("missing connection-handoff.json")
        shutil.copy2(handoff_src, OUT / "connection-handoff.json")
        shutil.copy2(LEGACY_OUT / "direct-core-results.json", OUT / "direct-core-results.json")
        shutil.copy2(LEGACY_OUT / "pod-meta.json", OUT / "pod-meta.json")
        shutil.copy2(LEGACY_OUT / "core-ready.json", OUT / "core-ready.json")
        results["steps"].append({"provision": True})

        # 2) Recover auth secret from pod process env
        log("recover_secret")
        rec = run([sys.executable, str(CORE_ROOT / "scripts/_phase5b2_recover_secret.py")], cwd=CORE_ROOT, timeout=180)
        (OUT / "recover-secret-stdout.txt").write_text(
            (rec.stdout or "").replace("SECRET", "[redacted-token]")[-2000:], encoding="utf-8"
        )
        legacy_secret = Path(tempfile.gettempdir()) / "phase5b2-cobra-core-auth.secret"
        if not legacy_secret.exists():
            raise RuntimeError("secret recover failed")
        SECRET_PATH.write_bytes(legacy_secret.read_bytes())
        secret = SECRET_PATH.read_text(encoding="utf-8").strip()
        if len(secret) < 8:
            raise RuntimeError("secret too short")
        results["steps"].append({"secret_recovered": True})

        # 3) Enable Computer staging via existing helper (writes 5b2 out; copy results)
        log("enable_computer_staging")
        env2 = os.environ.copy()
        env2["COBRA_CORE_AUTH_SECRET"] = secret
        env2["COBRA_COMPUTER_ROOT"] = str(COMPUTER_ROOT)
        # Patch computer staging OUT temporarily by running its steps inline via a thin wrapper.
        # Reuse _phase5b2_computer_staging but stop before its finally kill-switch by env flag.
        env2["PHASE5B3_DEFER_KILL_SWITCH"] = "1"
        # Monkeypatch: run computer staging script; it always kill-switches in finally.
        # Instead, call enable pieces directly here.
        sys.path.insert(0, str(CORE_ROOT / "scripts"))
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "phase5b2_computer", CORE_ROOT / "scripts/_phase5b2_computer_staging.py"
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        handoff = json.loads((OUT / "connection-handoff.json").read_text(encoding="utf-8"))
        mod.put_secret(secret)
        mod.patch_deploy_staging(True, handoff)
        patched = (COMPUTER_ROOT / "scripts" / "deploy-staging.mjs").read_text(encoding="utf-8")
        if "PHASE5B2_CORE_BEGIN" not in patched or handoff["COBRA_CORE_BASE_URL"] not in patched:
            raise RuntimeError("deploy-staging overlay missing after patch")
        build = run(["npm", "run", "build"], cwd=COMPUTER_ROOT, timeout=600)
        if build.returncode != 0:
            raise RuntimeError("computer build failed")
        # Re-assert overlay survived build (build must not rewrite deploy-staging.mjs).
        patched2 = (COMPUTER_ROOT / "scripts" / "deploy-staging.mjs").read_text(encoding="utf-8")
        if "PHASE5B2_CORE_BEGIN" not in patched2:
            raise RuntimeError("deploy-staging overlay lost after npm run build")
        deploy = run(["node", "scripts/deploy-staging.mjs"], cwd=COMPUTER_ROOT, timeout=900)
        (OUT / "computer-deploy-enable-stdout.txt").write_text((deploy.stdout or "")[-8000:], encoding="utf-8")
        if deploy.returncode != 0:
            raise RuntimeError("computer staging enable deploy failed")
        # Verify generated wrangler config actually carries Core enablement.
        wrangler_out = COMPUTER_ROOT / "dist" / "hidden_grid_os" / "wrangler.json"
        wrangler_txt = wrangler_out.read_text(encoding="utf-8") if wrangler_out.exists() else ""
        (OUT / "staging-wrangler-snippet.json").write_text(
            json.dumps(
                {
                    "has_enabled_true": '"COBRA_CORE_ENABLED": "true"' in wrangler_txt
                    or '"COBRA_CORE_ENABLED":"true"' in wrangler_txt,
                    "has_base_url": handoff["COBRA_CORE_BASE_URL"] in wrangler_txt,
                    "has_admin_only": "COBRA_CORE_ADMIN_ONLY" in wrangler_txt,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        if handoff["COBRA_CORE_BASE_URL"] not in wrangler_txt:
            raise RuntimeError("generated staging wrangler.json missing COBRA_CORE_BASE_URL")
        results["steps"].append({"staging_enable": True})
        results["staging_enable_version"] = None
        for line in (deploy.stdout or "").splitlines():
            if "Current Version ID:" in line:
                results["staging_enable_version"] = line.split(":", 1)[1].strip()

        # 4) Auth session proof against real Worker
        log("auth_session_proof")
        proof = run(
            ["npm", "run", "cobra-core:auth-session-proof", "--", "--staging"],
            cwd=COMPUTER_ROOT,
            env={"COBRA_CORE_STAGING_MARKER": "staging"},
            timeout=900,
        )
        (OUT / "auth-session-proof-stdout.txt").write_text((proof.stdout or "")[-8000:], encoding="utf-8")
        (OUT / "auth-session-proof-stderr.txt").write_text((proof.stderr or "")[-4000:], encoding="utf-8")
        # Copy computer evidence into Core evidence dir
        comp_ev = COMPUTER_ROOT / "evaluations/diagnostics/phase-5b3-authenticated-session"
        if comp_ev.is_dir():
            for f in comp_ev.glob("*"):
                if f.is_file():
                    shutil.copy2(f, OUT / f.name)
        results["steps"].append({"auth_session_proof": proof.returncode == 0, "exit": proof.returncode})
        if proof.returncode != 0:
            raise RuntimeError("auth-session-proof failed")

        # 5) Kill-switch: disable staging Core, redeploy, delete secret
        log("kill_switch")
        mod.patch_deploy_staging(False, handoff)
        build2 = run(["npm", "run", "build"], cwd=COMPUTER_ROOT, timeout=600)
        deploy2 = run(["node", "scripts/deploy-staging.mjs"], cwd=COMPUTER_ROOT, timeout=900)
        (OUT / "computer-deploy-disable-stdout.txt").write_text((deploy2.stdout or "")[-4000:], encoding="utf-8")
        ks = run(
            ["npm", "run", "cobra-core:kill-switch", "--", "--staging", "--dry-run"],
            cwd=COMPUTER_ROOT,
            timeout=180,
        )
        (OUT / "kill-switch-stdout.txt").write_text((ks.stdout or "")[-4000:], encoding="utf-8")
        mod.delete_secret()
        mod.put_secret(os.urandom(24).hex())
        mod.delete_secret()
        results["steps"].append(
            {
                "kill_switch": True,
                "deploy_disable_rc": deploy2.returncode,
                "kill_switch_rc": ks.returncode,
            }
        )
        for line in (deploy2.stdout or "").splitlines():
            if "Current Version ID:" in line:
                results["staging_disable_version"] = line.split(":", 1)[1].strip()

        results["ok"] = True
        return 0
    except Exception as exc:
        results["ok"] = False
        results["error"] = {"type": type(exc).__name__, "message": str(exc)[:400]}
        log("FAILED", results["error"])
        return 1
    finally:
        # Always terminate GPU + wipe local secret
        try:
            term = run([sys.executable, str(CORE_ROOT / "scripts/_phase5b2_terminate.py")], cwd=CORE_ROOT, timeout=180)
            (OUT / "terminate-stdout.txt").write_text((term.stdout or "")[-2000:], encoding="utf-8")
            results["terminate_rc"] = term.returncode
        except Exception as exc:
            results["terminate_error"] = type(exc).__name__
            log("terminate_error", type(exc).__name__)
        # Ensure staging disabled even on failure mid-flight
        try:
            handoff_path = OUT / "connection-handoff.json"
            if handoff_path.exists() and COMPUTER_ROOT.is_dir():
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "phase5b2_computer_finally", CORE_ROOT / "scripts/_phase5b2_computer_staging.py"
                )
                assert spec and spec.loader
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
                mod.patch_deploy_staging(False, handoff)
                run(["npm", "run", "build"], cwd=COMPUTER_ROOT, timeout=600)
                run(["node", "scripts/deploy-staging.mjs"], cwd=COMPUTER_ROOT, timeout=900)
                mod.delete_secret()
        except Exception as exc:
            results["finally_disable_error"] = type(exc).__name__
        for p in (SECRET_PATH, Path(tempfile.gettempdir()) / "phase5b2-cobra-core-auth.secret"):
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass
        results["ended_at"] = datetime.now(UTC).isoformat()
        write_json(OUT / "orchestrate-results.json", results)
        log("orchestrate_done", results.get("ok"))


if __name__ == "__main__":
    raise SystemExit(main())
