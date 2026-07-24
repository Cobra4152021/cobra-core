#!/usr/bin/env python3
"""Post-qualification freeze export for Phase 3F (no runtime behavior changes)."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = "0a2af49ee86451c374a600579d3644c811cd12c0"
TAG = "phase-3f-qualified"
OUT = ROOT / "docs/releases/phase-3f"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def main() -> int:
    head = subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT}", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    if head != EVIDENCE:
        # Allow freeze commit after tag; evidence SHA is recorded explicitly.
        print(f"note: HEAD={head} evidence={EVIDENCE}", flush=True)

    status = subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT}", "status", "--porcelain"],
        cwd=ROOT,
        text=True,
    )
    # Ignore this script / OUT if regenerating; require otherwise clean at start of freeze.
    dirty = [
        line
        for line in status.splitlines()
        if line.strip()
        and "docs/releases/" not in line
        and "_phase3f_freeze_release.py" not in line
        and "RELEASE_NOTES_Phase3F.md" not in line
    ]
    if dirty:
        print("repository not clean:", flush=True)
        print("\n".join(dirty), flush=True)
        return 2

    # Tag evidence commit (idempotent)
    existing = subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT}", "tag", "-l", TAG],
        cwd=ROOT,
        text=True,
    ).strip()
    if existing == TAG:
        tagged = subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT}", "rev-list", "-n", "1", TAG],
            cwd=ROOT,
            text=True,
        ).strip()
        if tagged != EVIDENCE:
            print(f"tag {TAG} points to {tagged}, expected {EVIDENCE}", flush=True)
            return 3
        print(f"tag exists: {TAG} -> {EVIDENCE}", flush=True)
    else:
        subprocess.check_call(
            [
                "git",
                "-c",
                f"safe.directory={ROOT}",
                "tag",
                "-a",
                TAG,
                EVIDENCE,
                "-m",
                "Phase 3F cloud Linux runtime qualified (Outcome A)",
            ],
            cwd=ROOT,
        )
        print(f"created tag: {TAG} -> {EVIDENCE}", flush=True)

    # Verify frozen benchmark facts
    protocol = json.loads(
        (ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json").read_text(
            encoding="utf-8"
        )
    )
    if protocol.get("status") != "prepared-not-run":
        print("protocol status mismatch", protocol.get("status"), flush=True)
        return 4
    v01 = (ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_1.md").read_text(encoding="utf-8")
    if "0.840" not in v01:
        print("official score 0.840 not found", flush=True)
        return 5
    outcome = json.loads(
        (
            ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/OUTCOME.json"
        ).read_text(encoding="utf-8")
    )
    if outcome.get("outcome") != "A" or outcome.get("benchmark_executed") is not False:
        print("outcome gate failed", flush=True)
        return 6

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # Run quality suite and capture results
    quality_log = OUT / "quality-suite-results.txt"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_quality.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    quality_log.write_text(
        (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else ""),
        encoding="utf-8",
    )
    quality_json = {
        "schema": "cobra.release.quality_suite_result.v1",
        "phase": "3F",
        "evidence_commit": EVIDENCE,
        "tag": TAG,
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "captured_at": datetime.now(UTC).isoformat(),
        "summary_line": next(
            (
                line
                for line in (proc.stdout or "").splitlines()
                if "passed" in line and "deselected" in line
            ),
            "",
        ),
        "all_checks_passed_marker": "OK: all quality checks passed" in (proc.stdout or ""),
    }
    (OUT / "quality-suite-results.json").write_text(
        json.dumps(quality_json, indent=2) + "\n", encoding="utf-8"
    )
    if proc.returncode != 0:
        print("quality suite failed; freeze aborted", flush=True)
        print((proc.stdout or "")[-2000:], flush=True)
        return 7

    exports: list[tuple[str, Path]] = [
        (
            "reports/QWEN3_8B_CLOUD_LINUX_RUNTIME_QUALIFICATION.md",
            ROOT / "evaluations/reports/QWEN3_8B_CLOUD_LINUX_RUNTIME_QUALIFICATION.md",
        ),
        (
            "reports/QWEN3_8B_PLATFORM_COMPARISON.md",
            ROOT / "evaluations/reports/QWEN3_8B_PLATFORM_COMPARISON.md",
        ),
        (
            "decisions/ADR-0014-cloud-linux-runtime-qualification.md",
            ROOT / "docs/decisions/ADR-0014-cloud-linux-runtime-qualification.md",
        ),
        (
            "diagnostics/OUTCOME.json",
            ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/OUTCOME.json",
        ),
        (
            "diagnostics/qualification_summary.json",
            ROOT
            / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/qualification_summary.json",
        ),
        (
            "diagnostics/environment.json",
            ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/environment.json",
        ),
        (
            "diagnostics/manifest.json",
            ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/manifest.json",
        ),
        (
            "diagnostics/native-backend-validation.json",
            ROOT
            / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/native-backend-validation.json",
        ),
        (
            "diagnostics/nvidia-smi.txt",
            ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/nvidia-smi.txt",
        ),
        (
            "runtime-candidate/qwen3-8b-cloud-linux-qualified.json",
            ROOT / "evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json",
        ),
        (
            "environment/requirements-cloud-lock.txt",
            ROOT / "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-lock.txt",
        ),
        (
            "environment/dependency-lock.sha256",
            ROOT / "evaluations/environments/cloud-qwen3-runtime/dependency-lock.sha256",
        ),
        (
            "environment/pip-freeze.txt",
            ROOT / "evaluations/environments/cloud-qwen3-runtime/pip-freeze.txt",
        ),
        (
            "environment/selection-rationale.md",
            ROOT / "evaluations/environments/cloud-qwen3-runtime/selection-rationale.md",
        ),
        (
            "cloud/authorization-record.json",
            ROOT / "evaluations/cloud/authorization-record.json",
        ),
        (
            "cloud/cost-record.json",
            ROOT / "evaluations/cloud/cost-record.json",
        ),
        (
            "cloud/cleanup-verification.json",
            ROOT / "evaluations/cloud/cleanup-verification.json",
        ),
        (
            "cloud/export-verification.json",
            ROOT / "evaluations/cloud/export-verification.json",
        ),
        (
            "protocol/qwen3-8b-cobrabench-v0.2-rc2.status.json",
            ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json",
        ),
    ]

    # Copy attempt summaries (results only; keep package bounded)
    attempts_root = ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/attempts"
    for attempt_dir in sorted(attempts_root.iterdir()):
        if not attempt_dir.is_dir():
            continue
        for name in ("result.json", "attempt.json", "smoke-output.txt"):
            src = attempt_dir / name
            if src.is_file():
                exports.append((f"diagnostics/attempts/{attempt_dir.name}/{name}", src))

    artifact_records = []
    for rel, src in exports:
        if not src.is_file():
            print("missing source", src, flush=True)
            return 8
        dest = OUT / rel
        copy_file(src, dest)
        digest = sha256_file(dest)
        artifact_records.append(
            {
                "path": rel.replace("\\", "/"),
                "sha256": digest,
                "size_bytes": dest.stat().st_size,
                "source": str(src.relative_to(ROOT)).replace("\\", "/"),
            }
        )

    # Include quality outputs already written
    for rel in ("quality-suite-results.txt", "quality-suite-results.json"):
        path = OUT / rel
        artifact_records.append(
            {
                "path": rel,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "source": "generated-during-freeze",
            }
        )

    release_notes = f"""# RELEASE NOTES — Phase 3F

**Tag:** `{TAG}`  
**Evidence commit:** `{EVIDENCE}`  
**Freeze generated:** {datetime.now(UTC).isoformat()}  
**Outcome:** A — Cloud Linux runtime fully qualified

## Infrastructure used

| Field | Value |
| --- | --- |
| Provider | RunPod Community Cloud |
| Pod ID | `txw75nv9hn96hu` (adopted; no second pod created) |
| GPU | NVIDIA A40 48 GB |
| Displayed hourly rate | $0.44/hr |
| System RAM | 50 GB |
| Storage | 50 GB volume + 30 GB container (model/repo on `/workspace`) |
| OS / kernel | Ubuntu 24.04 template base / `5.15.0-94-generic` |
| Access | SSH over exposed TCP (runpodctl key) after `PUBLIC_KEY` injection |
| Estimated spend | ~$1.38 over ~3.14 h (ceiling $10 respected) |
| Cleanup | Pod terminated; zero remaining billable Phase 3F resources |

## Qualification results

| Gate | Result |
| --- | --- |
| Native CUDA / bitsandbytes backend | pass |
| Initial full load | pass |
| Initial synthetic generation | pass |
| 3/3 fresh-process qualification | pass |
| Extended session (5 prompts) | pass |
| Full-load budget used | 6 / 6 |
| Peak VRAM | ~5.88 GiB |
| Model revision | `{MODEL_REV}` |
| Model inventory hash | `{MODEL_INV}` |
| Runtime candidate | `evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json` |

CobraBench was **not** executed. Prepared rc2 protocol remains `prepared-not-run`.  
Official CobraBench v0.1 score remains **0.840**.

## Dependency changes

Cloud lock aligned to the validated Python 3.12 inference freeze before install:

* `huggingface-hub` corrected from `0.34.4` → `1.24.0` (required by `transformers==5.14.1`, `>=1.5.0`)
* `tokenizers` `0.22.1` → `0.22.2`
* `safetensors` `0.5.3` → `0.8.0`
* `numpy` `2.2.6` → `2.5.1`
* `psutil` `7.0.0` → `7.2.2`
* `pytest` `8.4.1` → `8.4.2`
* torch installed as `2.6.0+cu124` from the official cu124 wheel index

Pinned stack used in qualification: Python 3.12.3, torch 2.6.0+cu124, transformers 5.14.1, accelerate 1.14.0, bitsandbytes 0.49.2.

## Known limitations

* Qualification used synthetic smoke prompts only (not CobraBench cases).
* Runtime candidate is prospective; it is not added to a frozen runtime registry beyond this release package.
* Adopted GPU was A40 (user pod), not the originally preferred L4 SKU; still within the $10 / 8h authorization.
* Host overlay disk (~30 GB) is insufficient for model + venv; Linux-native `/workspace` storage was required.
* Phase 3G (controlled CobraBench v0.2-rc2 on this locked runtime) is authorized next but **not started**.

## Next authorized phase

**Phase 3G — controlled CobraBench v0.2-rc2 execution on the locked cloud runtime**

Do not train, deploy, or designate Cobra Core without a separate authorization.
"""
    notes_path = OUT / "RELEASE_NOTES_Phase3F.md"
    notes_path.write_text(release_notes, encoding="utf-8")
    artifact_records.append(
        {
            "path": "RELEASE_NOTES_Phase3F.md",
            "sha256": sha256_file(notes_path),
            "size_bytes": notes_path.stat().st_size,
            "source": "generated-during-freeze",
        }
    )

    final_report = f"""# Phase 3F Release Report

## Verdict

**Qualified.** Tag `{TAG}` freezes evidence commit `{EVIDENCE}` (Outcome A).

## Freeze contents

Package root: `docs/releases/phase-3f/`

Includes runtime qualification report, environment versions, dependency lockfiles, runtime candidate JSON, quality suite results, attempt evidence, cloud cost/cleanup records, release notes, and this report.

## Integrity

* CobraBench v0.2-rc2 protocol: `prepared-not-run`
* Official CobraBench v0.1 score: **0.840** (unchanged)
* Quality suite at freeze: **passed** (`{quality_json["summary_line"]}`)
* Benchmark executed during Phase 3F: **false**

## Operations summary

* Adopted RunPod pod `txw75nv9hn96hu` (A40, $0.44/hr); no second instance
* 6/6 full-load qualification sequence passed
* Estimated spend ~$1.38; pod terminated; remaining billable resources: none

## Next step

Phase 3G is the next authorized phase. It is **not** started by this freeze.
"""
    report_path = OUT / "PHASE_3F_RELEASE_REPORT.md"
    report_path.write_text(final_report, encoding="utf-8")
    artifact_records.append(
        {
            "path": "PHASE_3F_RELEASE_REPORT.md",
            "sha256": sha256_file(report_path),
            "size_bytes": report_path.stat().st_size,
            "source": "generated-during-freeze",
        }
    )

    # Evidence manifest lists content artifacts (not SHA256SUMS).
    artifact_records = sorted(artifact_records, key=lambda r: r["path"])
    manifest_path = OUT / "EVIDENCE_MANIFEST.json"
    final_manifest = {
        "schema": "cobra.release.evidence_manifest.v1",
        "phase": "3F",
        "tag": TAG,
        "evidence_commit": EVIDENCE,
        "freeze_generated_at": datetime.now(UTC).isoformat(),
        "outcome": "A",
        "outcome_label": "Cloud Linux runtime fully qualified",
        "model_revision": MODEL_REV,
        "model_inventory_hash": MODEL_INV,
        "cobrabench_v02_rc2_status": "prepared-not-run",
        "official_v01_score": "0.840",
        "benchmark_executed": False,
        "quality_suite_passed": True,
        "quality_suite_summary": quality_json["summary_line"],
        "artifact_count": len(artifact_records),
        "artifacts": artifact_records,
        "sha256sums_file": "SHA256SUMS",
        "notes": [
            "Freeze package does not modify runtime behavior.",
            "Phase 3G not started.",
            "Tag phase-3f-qualified points at evidence commit "
            "0a2af49ee86451c374a600579d3644c811cd12c0.",
            "Verify package with SHA256SUMS (covers all files except itself).",
        ],
    }
    manifest_path.write_text(json.dumps(final_manifest, indent=2) + "\n", encoding="utf-8")

    # SHA256SUMS covers every package file except itself.
    sha_path = OUT / "SHA256SUMS"
    all_files = sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    sha_path.write_text(
        "\n".join(f"{sha256_file(p)}  {p.relative_to(OUT).as_posix()}" for p in all_files) + "\n",
        encoding="utf-8",
    )

    print("freeze_complete", OUT, "hashed_files", len(all_files), flush=True)
    print("protocol", protocol["status"], "score_marker", "0.840", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
