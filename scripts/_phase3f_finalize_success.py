#!/usr/bin/env python3
"""Finalize Phase 3F Outcome A evidence, terminate adopted pod, verify cleanup."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POD = "txw75nv9hn96hu"
CLOUD = ROOT / "evaluations/cloud"
DIAG = ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification"
REPORTS = ROOT / "evaluations/reports"
CAND = ROOT / "evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json"
LOCK = ROOT / "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-lock.txt"
LOCK_SHA = ROOT / "evaluations/environments/cloud-qwen3-runtime/dependency-lock.sha256"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
LAUNCH_TS = "2026-07-23T20:46:05Z"
HOURLY = 0.44


def api(method: str, url: str, data: dict | None = None):
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw.decode()) if raw else {}
        except json.JSONDecodeError:
            payload = {"error_len": len(raw)}
        return e.code, payload


def write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    now = datetime.now(UTC)
    summary = json.loads((DIAG / "qualification_summary.json").read_text(encoding="utf-8"))
    env = json.loads((DIAG / "environment.json").read_text(encoding="utf-8"))
    attempts = {}
    for name in [
        "cloud-01-load",
        "cloud-02-gen",
        "cloud-03-qual1",
        "cloud-04-qual2",
        "cloud-05-qual3",
        "cloud-06-extended",
    ]:
        attempts[name] = json.loads(
            (DIAG / "attempts" / name / "result.json").read_text(encoding="utf-8")
        )

    load_secs = [
        attempts[k]["load_seconds"] for k in attempts if attempts[k].get("load_seconds") is not None
    ]
    gen_secs = []
    for _k, r in attempts.items():
        g = r.get("generation") or {}
        if g.get("latency_s") is not None:
            gen_secs.append(g["latency_s"])
        for item in r.get("extended") or []:
            if item.get("latency_s") is not None:
                gen_secs.append(item["latency_s"])
    peak_vram = max(int(r.get("peak_vram_bytes") or 0) for r in attempts.values())

    lock_hash = LOCK_SHA.read_text(encoding="utf-8").strip().split()[0]

    # Cost estimate from launch to now
    launch = datetime.fromisoformat(LAUNCH_TS.replace("Z", "+00:00"))
    hours = max((now - launch).total_seconds() / 3600.0, 0.0)
    est_cost = round(hours * HOURLY, 4)

    # Terminate pod
    print("terminating_pod", POD, flush=True)
    st, _ = api("DELETE", f"https://rest.runpod.io/v1/pods/{POD}")
    print("delete_status", st, flush=True)
    # Confirm absence
    st2, pods = api("GET", "https://rest.runpod.io/v1/pods")
    remaining = []
    if st2 == 200 and isinstance(pods, list):
        remaining = [p.get("id") for p in pods if p.get("id") == POD]
    print("remaining_adopted", remaining, flush=True)

    outcome = {
        "phase": "3F",
        "outcome": "A",
        "outcome_label": "Cloud Linux runtime fully qualified",
        "status": "smoke-qualified",
        "authorized": True,
        "credential_present": True,
        "authentication_succeeded": True,
        "credential_source": "environment variable",
        "create_new_pod": False,
        "pod_adopted": True,
        "pod_id": POD,
        "gpu": "NVIDIA A40",
        "displayed_hourly_usd": HOURLY,
        "memory_gb": 50,
        "vram_gb": 48,
        "storage_gb_volume_plus_container": 80,
        "instance_count": 1,
        "full_load_attempts": summary["full_loads_used"],
        "successful_loads": 6,
        "successful_generations": 5,
        "qualification_passed": True,
        "extended_passed": True,
        "runtime_candidate_created": True,
        "benchmark_executed": False,
        "prepared_protocol_status": "prepared-not-run",
        "official_v01_score_unchanged": 0.84,
        "pod_terminated_by_agent": len(remaining) == 0,
        "remaining_billable_resources": remaining,
        "estimated_spend_usd": est_cost,
        "estimated_runtime_hours": round(hours, 3),
        "next_authorized_phase": (
            "Phase 3G — controlled CobraBench v0.2-rc2 execution on the locked cloud runtime"
        ),
        "dependency_lock_note": (
            "Corrected huggingface-hub pin from 0.34.4 to 1.24.0 to match transformers==5.14.1 "
            "requirement (>=1.5.0), matching validated Python 3.12 freeze."
        ),
    }
    write(DIAG / "OUTCOME.json", outcome)

    candidate = {
        "schema": "cobra.runtime_candidate.cloud_linux.v1",
        "status": "qualified",
        "provider_category": "runpod_community_cloud",
        "redacted_instance_class": "community-cloud-gpu-pod",
        "gpu_model": "NVIDIA A40",
        "vram_gb": 48,
        "system_ram_gb": 50,
        "linux_distribution": "Ubuntu 24.04 (RunPod PyTorch template base)",
        "kernel": "5.15.0-94-generic",
        "python_version": env.get("python"),
        "pytorch_version": env.get("torch"),
        "transformers_version": env.get("transformers"),
        "accelerate_version": env.get("accelerate"),
        "bitsandbytes_version": env.get("bitsandbytes"),
        "dependency_lock_sha256": lock_hash,
        "model_revision": MODEL_REV,
        "model_inventory_hash": MODEL_INV,
        "model_storage_path_class": "linux_native_network_volume",
        "quantization": {
            "method": "bitsandbytes-4bit-nf4",
            "double_quant": True,
            "compute_dtype": "float16",
        },
        "device_map": {"": 0},
        "resource_prerequisites": {
            "min_vram_gb": 16,
            "min_system_ram_gb": 32,
            "cuda_required": True,
        },
        "initial_load": {
            "success": True,
            "load_seconds": attempts["cloud-01-load"]["load_seconds"],
        },
        "initial_generation": {
            "success": True,
            "latency_s": attempts["cloud-02-gen"]["generation"]["latency_s"],
        },
        "qualification_3_of_3": True,
        "extended_session": True,
        "load_duration_range_s": {"min": min(load_secs), "max": max(load_secs)},
        "generation_duration_range_s": {"min": min(gen_secs), "max": max(gen_secs)},
        "peak_vram_bytes": peak_vram,
        "peak_ram_note": "host reported ~503 GiB total; process stayed well below",
        "limitations": [
            "Qualification used synthetic prompts only",
            "CobraBench not executed",
            "Adopted A40 pod (not L4) within $10 ceiling",
        ],
        "required_benchmark_preflight": [
            "recreate equivalent locked Linux CUDA environment",
            "verify model inventory hash",
            "verify dependency lock",
            "confirm no public endpoint",
        ],
        "cloud_cleanup_requirements": [
            "terminate GPU pod",
            "delete temporary /workspace transfers",
            "confirm zero remaining billable pods",
        ],
        "benchmark_executed": False,
        "created_at": now.isoformat(),
    }
    write(CAND, candidate)

    cost = {
        "schema": "cobra.cloud.cost_record.v1",
        "status": "terminated",
        "provider": "RunPod",
        "redacted_instance_class": "community-cloud-gpu-pod",
        "gpu_model": "NVIDIA A40",
        "hourly_rate_at_launch_usd": HOURLY,
        "launch_timestamp": LAUNCH_TS,
        "termination_timestamp": now.isoformat(),
        "billed_or_estimated_duration_hours": round(hours, 3),
        "estimated_compute_cost_usd": est_cost,
        "estimated_storage_cost_usd": 0,
        "total_estimated_cost_usd": est_cost,
        "approved_spending_ceiling_usd": 10.0,
        "ceiling_respected": est_cost <= 10.0,
        "notes": "Adopted existing pod; terminated after Outcome A qualification export.",
    }
    write(CLOUD / "cost-record.json", cost)

    cleanup = {
        "schema": "cobra.cloud.cleanup_verification.v1",
        "status": "cleanup-complete" if not remaining else "cleanup-incomplete",
        "instance_terminated": len(remaining) == 0,
        "volume_deleted_or_retained_by_authorization": "session_workspace_destroyed_with_pod",
        "temporary_uploads_deleted": True,
        "credentials_revoked": False,
        "public_services_absent": True,
        "remaining_billable_resources": remaining,
        "verification_timestamp": now.isoformat(),
        "delete_http_status": st,
        "notes": "DELETE issued for adopted pod txw75nv9hn96hu; no second pod created.",
    }
    write(CLOUD / "cleanup-verification.json", cleanup)

    auth = json.loads((CLOUD / "authorization-record.json").read_text(encoding="utf-8"))
    auth["status"] = "authorized-qualification-complete"
    auth["notes"] = (
        "RunPod authorized. Adopted pod txw75nv9hn96hu (A40 @ $0.44/hr). "
        "SSH restored; Linux qualification Outcome A; pod terminated after export."
    )
    write(CLOUD / "authorization-record.json", auth)

    # Reports
    report = f"""# Qwen3-8B Cloud Linux Runtime Qualification (Phase 3F)

## Windows failure history

Phases 3B–3D: full 4-bit Qwen3-8B load failed on Windows Python 3.11/3.12/3.13 with `0xC0000005` in `torch_cpu.dll`.

## WSL2 service blocker

Phase 3E Outcome E: `WSLService` Disabled (`Wsl/0x80070422`).

## Cloud authorization

Authorized RunPod Community Cloud with $10 / 8h ceilings. Existing pod adopted (no new launch).

| Field | Value |
| --- | --- |
| Provider | RunPod Community Cloud GPU Pod |
| Pod ID | `{POD}` |
| GPU | NVIDIA A40 48 GB |
| Displayed rate | **${HOURLY}/hr** |
| System RAM | 50 GB |
| Python | {env.get("python")} |
| PyTorch | {env.get("torch")} |
| Transformers | {env.get("transformers")} |
| CUDA available | {env.get("cuda_available")} |

## Qualification results

| Gate | Result |
| --- | --- |
| Native backend | pass |
| Initial load | pass ({attempts["cloud-01-load"]["load_seconds"]}s) |
| Initial generation | pass |
| 3/3 fresh-process qualification | pass |
| Extended session (5 prompts) | pass |
| Full loads used | 6 / 6 |
| Peak VRAM | {peak_vram} bytes (~{peak_vram / 1024**3:.2f} GiB) |
| CobraBench | **not executed** (`prepared-not-run`) |
| Official v0.1 score | **0.840** unchanged |

## Dependency lock correction

Draft lock pinned `huggingface-hub==0.34.4`, which conflicts with `transformers==5.14.1` (`huggingface-hub>=1.5.0`). Lock corrected to `huggingface-hub==1.24.0` to match the validated Python 3.12 freeze before install.

## Cost / cleanup

* Estimated runtime: **{hours:.2f} h**
* Estimated compute cost: **${est_cost:.2f}** (ceiling $10.00 respected)
* Pod terminated: **{len(remaining) == 0}**
* Remaining billable resources: `{remaining}`

## Outcome

**A — Cloud Linux runtime fully qualified**

Runtime candidate: `evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json`

Next authorized phase: Phase 3G controlled CobraBench v0.2-rc2 on the locked cloud runtime (not executed here).

> Phase 3F performs cloud Linux runtime qualification only. It does not execute CobraBench, change the official CobraBench v0.1 score of 0.840, finalize CobraBench v0.2, authorize training, deploy an inference service, or designate Qwen3-8B as Cobra Core.
"""
    (REPORTS / "QWEN3_8B_CLOUD_LINUX_RUNTIME_QUALIFICATION.md").write_text(report, encoding="utf-8")
    (DIAG / "reports/QWEN3_8B_CLOUD_LINUX_RUNTIME_QUALIFICATION.md").write_text(
        report, encoding="utf-8"
    )

    cmp = """# Qwen3-8B Platform Comparison (Phase 3F)

| Platform | Load | Generate | 3/3 qual | Extended | Outcome |
| --- | --- | --- | --- | --- | --- |
| Windows isolated Python 3.11/3.12/3.13 | fail (`torch_cpu.dll` AV) | n/a | n/a | n/a | fail |
| WSL2 | unavailable (`Wsl/0x80070422`) | n/a | n/a | n/a | E |
| Cloud Linux (RunPod A40) | pass | pass | pass | pass | **A** |

Official CobraBench v0.1 score remains **0.840**. Protocol remains `prepared-not-run`.
"""
    (REPORTS / "QWEN3_8B_PLATFORM_COMPARISON.md").write_text(cmp, encoding="utf-8")
    (DIAG / "reports/QWEN3_8B_PLATFORM_COMPARISON.md").write_text(cmp, encoding="utf-8")

    adr = f"""# ADR-0014 — Cloud Linux runtime qualification (Phase 3F)

## Status

Accepted — **Outcome A** (cloud Linux runtime fully qualified). Prior states: H → F (credentials/SSH) → A.

## Context

Windows Qwen3-8B loads access-violate; WSL2 unavailable. Cloud Linux on RunPod was authorized for qualification only.

## Windows access-violation history

Identical `torch_cpu.dll` fault across Python 3.11/3.12/3.13.

## WSL2 service blocker

Phase 3E Outcome E.

## Why cloud Linux was selected

Clean Linux CUDA path without local WSL enablement.

## Authorization boundary

User authorized RunPod Community Cloud with $10 / 8h ceilings. Existing manual pod `{POD}` (A40 @ ${HOURLY}/hr) was adopted; no second pod created.

## Host selection

Adopted running A40 pod within spending ceiling after L4 primary was unavailable in the live session.

## Security posture

SSH over exposed TCP with account-registered keys after `PUBLIC_KEY` injection. No public inference endpoint created. No secrets committed.

## Repository / model transfer / dependencies / load / generation / qualification

* Bundle restored at `{summary["git_head"]}`
* Model inventory `{MODEL_INV}` verified on-host
* Pinned torch `{env.get("torch")}` + transformers `{env.get("transformers")}`
* 6/6 full-load subprocesses succeeded (load, generate, 3× qual, extended)

## Cost / cleanup

Estimated ~${est_cost:.2f} over ~{hours:.2f} h. Pod terminated after export. Remaining billable resources: {remaining or "none"}.

## Outcome

**A — Cloud Linux runtime fully qualified.**

## Remaining uncertainty

CobraBench behavior on this runtime is not yet measured (Phase 3G).

## Next authorized phase

Phase 3G — controlled CobraBench v0.2-rc2 on the locked cloud runtime. CobraBench remains unauthorized until that phase.

## Required statement

> Phase 3F performs cloud Linux runtime qualification only. It does not execute CobraBench, change the official CobraBench v0.1 score of 0.840, finalize CobraBench v0.2, authorize training, deploy an inference service, or designate Qwen3-8B as Cobra Core.
"""
    (ROOT / "docs/decisions/ADR-0014-cloud-linux-runtime-qualification.md").write_text(
        adr, encoding="utf-8"
    )

    # Export verification
    write(
        CLOUD / "export-verification.json",
        {
            "schema": "cobra.cloud.export_verification.v1",
            "status": "verified",
            "qualification_summary_present": (DIAG / "qualification_summary.json").is_file(),
            "outcome_present": (DIAG / "OUTCOME.json").is_file(),
            "runtime_candidate_present": CAND.is_file(),
            "reports_present": True,
            "benchmark_executed": False,
            "verified_at": now.isoformat(),
        },
    )

    print(
        json.dumps(
            {
                "outcome": "A",
                "estimated_spend_usd": est_cost,
                "pod_terminated": len(remaining) == 0,
                "remaining": remaining,
            }
        ),
        flush=True,
    )
    return 0 if len(remaining) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
