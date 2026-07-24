"""Phase 3G Priority 1 static tests (no cloud spend, no model load)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "evaluations/environments/cloud-qwen3-runtime"
DIAG = ROOT / "evaluations/diagnostics/phase-3g-p1"
PROTOCOL = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"
BASELINE = "0a2af49ee86451c374a600579d3644c811cd12c0"


def test_protocol_and_score_unchanged() -> None:
    assert json.loads(PROTOCOL.read_text(encoding="utf-8"))["status"] == "prepared-not-run"
    assert "0.840" in (ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_1.md").read_text(
        encoding="utf-8"
    )


def test_runtime_and_dev_locks_split() -> None:
    runtime = (ENV / "requirements-cloud-runtime.txt").read_text(encoding="utf-8")
    dev = (ENV / "requirements-cloud-dev.txt").read_text(encoding="utf-8")
    lock = (ENV / "requirements-cloud-lock.txt").read_text(encoding="utf-8")
    assert "pytest" not in runtime
    assert "pytest==8.4.2" in dev
    assert "transformers==5.14.1" in runtime
    assert "bitsandbytes==0.49.2" in runtime
    assert "transformers==5.14.1" in lock
    for text in (runtime, lock):
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            assert ">=" not in s and "~=" not in s
            assert s.count("==") == 1, s


def test_torch_and_image_pins() -> None:
    torch_pin = json.loads((ENV / "torch-pin.json").read_text(encoding="utf-8"))
    image = json.loads((ENV / "container-image-pin.json").read_text(encoding="utf-8"))
    assert torch_pin["torch"] == "2.6.0+cu124"
    assert "pytorch.org" in torch_pin["index_url"]
    assert image["qualified_commit"] == BASELINE
    assert image["digest_amd64"].startswith("sha256:")
    assert "runpod/pytorch" in image["image_name"]


def test_dependency_lock_hashes_cover_split_files() -> None:
    text = (ENV / "dependency-lock.sha256").read_text(encoding="utf-8")
    assert "requirements-cloud-runtime.txt" in text
    assert "requirements-cloud-lock.txt" in text
    assert "requirements-cloud-dev.txt" in text


def test_operator_scripts_exist_and_refuse_secrets_logging() -> None:
    scripts = [
        "scripts/phase3g_ssh_bootstrap.py",
        "scripts/phase3g_provision_preflight.py",
        "scripts/phase3g_cleanup_verify.py",
        "scripts/phase3g_verify_env.py",
        "scripts/phase3g_write_p1_evidence.py",
    ]
    for rel in scripts:
        path = ROOT / rel
        assert path.is_file(), rel
        text = path.read_text(encoding="utf-8")
        assert "print(key)" not in text
        assert "RUNPOD_API_KEY)" not in text or "os.environ" in text
        # must not write API key values into JSON examples
        assert "rpa_" not in text


def test_vram_and_cost_docs() -> None:
    vram = (ENV / "VRAM_ENVELOPE.md").read_text(encoding="utf-8")
    cost = (ENV / "GPU_COST_RECOMMENDATIONS.md").read_text(encoding="utf-8")
    assert "5.88" in vram or "6,318,342,144" in vram
    assert "16 GB" in vram
    assert "L4" in cost and "A5000" in cost
    assert "$0.44" in cost


def test_p1_evidence_summary() -> None:
    summary = json.loads((DIAG / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["baseline_commit"] == BASELINE
    assert summary["benchmark_executed"] is False
    assert summary["runtime_requalification_required"] is False
    assert summary["official_v01_score_unchanged"] == 0.84
    assert len(summary["tasks"]) == 10
    integrity = json.loads((DIAG / "integrity-check.json").read_text(encoding="utf-8"))
    assert integrity["cobrabench_v02_rc2_status"] == "prepared-not-run"
    assert integrity["official_score_marker_present"] is True


def test_adr_and_implementation_record() -> None:
    adr = (ROOT / "docs/decisions/ADR-0015-phase-3g-runtime-ops-hardening.md").read_text(
        encoding="utf-8"
    )
    impl = (ROOT / "docs/phases/PHASE_3G_P1_IMPLEMENTATION.md").read_text(encoding="utf-8")
    assert "Priority 1" in adr
    assert "0.840" in adr
    assert "Requal?" in impl
    assert "Not required" in (ROOT / "docs/phases/PHASE_3G_STATUS.md").read_text(encoding="utf-8")
