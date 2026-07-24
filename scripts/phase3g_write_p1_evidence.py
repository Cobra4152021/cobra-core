#!/usr/bin/env python3
"""Generate Phase 3G Priority-1 evidence package (docs/metadata only; no cloud spend)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "evaluations/diagnostics/phase-3g-p1"
BASELINE = "0a2af49ee86451c374a600579d3644c811cd12c0"
TAG = "phase-3f-qualified"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    DIAG.mkdir(parents=True, exist_ok=True)
    tasks = [
        {
            "id": "P1-01",
            "title": "Automate SSH bootstrap and qualification setup",
            "files": [
                "scripts/phase3g_ssh_bootstrap.py",
                "evaluations/environments/cloud-qwen3-runtime/creation-commands.md",
            ],
            "benefit": "Removes multi-step SSH PUBLIC_KEY recovery; faster session start",
            "risk": "Low — ops only; may restart pod if --restart used",
            "requalification_required": False,
        },
        {
            "id": "P1-02",
            "title": "Pin runtime dependencies and container image digests",
            "files": [
                "evaluations/environments/cloud-qwen3-runtime/torch-pin.json",
                "evaluations/environments/cloud-qwen3-runtime/container-image-pin.json",
                "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-runtime.txt",
                "evaluations/environments/cloud-qwen3-runtime/dependency-lock.sha256",
            ],
            "benefit": "Bit-identity for host image + venv pins; fewer silent skews",
            "risk": "Low — pins match Phase 3F qualified versions",
            "requalification_required": False,
        },
        {
            "id": "P1-03",
            "title": "Separate runtime vs development dependencies",
            "files": [
                "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-runtime.txt",
                "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-dev.txt",
                "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-lock.txt",
            ],
            "benefit": "Smaller production venv; pytest excluded from runtime path",
            "risk": "Low — runtime pins unchanged from 3F inference stack",
            "requalification_required": False,
        },
        {
            "id": "P1-04",
            "title": "Improve reproducibility of environment creation",
            "files": [
                "evaluations/environments/cloud-qwen3-runtime/creation-commands.md",
                "scripts/phase3g_verify_env.py",
                "evaluations/environments/cloud-qwen3-runtime/environment-manifest.json",
            ],
            "benefit": "Deterministic create path with verify step",
            "risk": "Low",
            "requalification_required": False,
        },
        {
            "id": "P1-05",
            "title": "Improve provisioning scripts",
            "files": ["scripts/phase3g_provision_preflight.py"],
            "benefit": "Hard gates before spend; single-instance / price / disk checks",
            "risk": "Low — does not create pods",
            "requalification_required": False,
        },
        {
            "id": "P1-06",
            "title": "Improve cleanup verification",
            "files": ["scripts/phase3g_cleanup_verify.py"],
            "benefit": "Reliable terminate + remaining-resource audit",
            "risk": "Low–Med if --terminate mis-targeted (requires explicit pod id)",
            "requalification_required": False,
        },
        {
            "id": "P1-07",
            "title": "Improve documentation",
            "files": [
                "docs/phases/PHASE_3G_P1_IMPLEMENTATION.md",
                "docs/phases/PHASE_3G_STATUS.md",
                "docs/decisions/ADR-0015-phase-3g-runtime-ops-hardening.md",
                "evaluations/environments/cloud-qwen3-runtime/README.md",
            ],
            "benefit": "Clear ops runbooks and governance",
            "risk": "None",
            "requalification_required": False,
        },
        {
            "id": "P1-08",
            "title": "Improve qualification evidence generation",
            "files": [
                "scripts/phase3g_write_p1_evidence.py",
                "evaluations/diagnostics/phase-3g-p1/",
            ],
            "benefit": "Structured P1 evidence with hashes and requal flags",
            "risk": "None",
            "requalification_required": False,
        },
        {
            "id": "P1-09",
            "title": "Document validated VRAM envelope",
            "files": ["evaluations/environments/cloud-qwen3-runtime/VRAM_ENVELOPE.md"],
            "benefit": "Enables safe SKU right-sizing without guessing",
            "risk": "None (docs)",
            "requalification_required": False,
        },
        {
            "id": "P1-10",
            "title": "Recommend lowest-cost supported GPU configurations",
            "files": ["evaluations/environments/cloud-qwen3-runtime/GPU_COST_RECOMMENDATIONS.md"],
            "benefit": "Guides cheaper L4/A5000 create path vs A40 adopt",
            "risk": "Low — recommendations only; new SKU needs abbreviated smoke later",
            "requalification_required": False,
        },
    ]

    file_hashes = {}
    for t in tasks:
        for rel in t["files"]:
            path = ROOT / rel
            if path.is_file():
                file_hashes[rel.replace("\\", "/")] = sha(path)
            elif path.is_dir():
                file_hashes[rel.replace("\\", "/")] = "directory"

    summary = {
        "schema": "cobra.diagnostics.phase3g_p1_summary.v1",
        "phase": "3G",
        "priority": 1,
        "status": "implemented-docs-and-tooling",
        "baseline_tag": TAG,
        "baseline_commit": BASELINE,
        "benchmark_executed": False,
        "prepared_protocol_status": "prepared-not-run",
        "official_v01_score_unchanged": 0.84,
        "model_behavior_changed": False,
        "inference_behavior_changed": False,
        "runtime_requalification_required": False,
        "runtime_requalification_rationale": (
            "P1 changes are operational tooling, dependency pinning identical to Phase 3F "
            "qualified versions, and documentation. No model/prompt/quantization/device_map changes."
        ),
        "estimated_cloud_savings": {
            "ops_only_per_session_usd": 0.22,
            "ops_note": "Approx. 30 minutes less avoidable GPU time at $0.44/hr",
            "sku_rightsize_per_hour_usd": 0.19,
            "sku_note": "Indicative A40 $0.44 vs A5000 ~$0.25 if authorized fallback used after smoke",
        },
        "tasks": tasks,
        "file_hashes": file_hashes,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    (DIAG / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (DIAG / "TASKS.json").write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")

    protocol = json.loads(
        (ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json").read_text(
            encoding="utf-8"
        )
    )
    integrity = {
        "schema": "cobra.diagnostics.phase3g_p1_integrity.v1",
        "cobrabench_v02_rc2_status": protocol.get("status"),
        "official_score_marker_present": "0.840"
        in (ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_1.md").read_text(encoding="utf-8"),
        "baseline_tag": TAG,
        "baseline_commit": BASELINE,
        "checked_at": datetime.now(UTC).isoformat(),
    }
    (DIAG / "integrity-check.json").write_text(
        json.dumps(integrity, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote", DIAG.as_posix(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
