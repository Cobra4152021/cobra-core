#!/usr/bin/env python3
"""Non-benchmark smoke generation for Qwen3-8B rc2 readiness."""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.evaluation.rc2_run import MANIFEST_PATH, sanitize_path, write_json  # noqa: E402
from cobra_core.inference.engine import LocalInferenceEngine  # noqa: E402
from cobra_core.providers.qwen_local import QwenLocalAdapter  # noqa: E402
from cobra_core.schemas.inference import InferenceRequest  # noqa: E402
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402

OUT = ROOT / "evaluations/smoke/qwen3-8b-rc2-readiness"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = ModelManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))
    # Prefer conservative defaults matching adapter/v0.1 path after ACCESS_VIOLATION
    # during a prior attempt with 9GiB GPU reservation under desktop VRAM contention.
    engine = LocalInferenceEngine(
        QwenLocalAdapter(
            load_in_4bit=True,
            max_memory={0: "8GiB", "cpu": "14GiB"},
        )
    )
    # Synthetic non-benchmark evidence prompt (must not duplicate rc2 cases).
    user = (
        "Using only the evidence below, answer in one short sentence.\n\n"
        "[SOURCE S1]\n"
        "Title: Lab Note\n"
        "Content:\n"
        "Date: 2026-07-01. The calibration lamp was replaced at 09:15.\n\n"
        "Question: What time was the calibration lamp replaced?"
    )
    req = InferenceRequest(
        system_prompt="Use only supplied evidence. Cite [S1] if stating a fact.",
        user_prompt=user,
        max_new_tokens=64,
        temperature=0.0,
        seed=123,
        enable_thinking=False,
    )
    started = datetime.now(UTC).isoformat()
    t0 = time.perf_counter()
    peak_vram = None
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
        load_t0 = time.perf_counter()
        result = engine.run(
            manifest=manifest,
            manifest_ref="model-cards/qwen/qwen3-8b.manifest.json",
            request=req,
            environment_reference="phase3b-smoke",
            results_dir=None,
            persist=False,
        )
        elapsed = time.perf_counter() - t0
        if torch.cuda.is_available():
            peak_vram = int(torch.cuda.max_memory_allocated())
        payload = {
            "status": "pass",
            "started_at": started,
            "ended_at": datetime.now(UTC).isoformat(),
            "load_and_generation_duration_s": round(elapsed, 3),
            "generation_latency_ms": result.total_latency_ms,
            "approx_load_duration_s": round(
                load_t0 and (elapsed - ((result.total_latency_ms or 0) / 1000.0)), 3
            ),
            "model_revision": manifest.model_revision,
            "artifact_root": sanitize_path(manifest.local_artifact_root or ""),
            "response": result.assistant_response,
            "finish_reason": result.finish_reason,
            "input_tokens": result.input_token_count,
            "output_tokens": result.output_token_count,
            "peak_vram_bytes": peak_vram,
            "error": result.error,
            "notes": "Non-benchmark synthetic prompt for readiness only.",
        }
        write_json(OUT / "smoke_result.json", payload)
        (OUT / "SMOKE.md").write_text(
            f"# RC2 readiness smoke\n\nStatus: **pass**\n\nResponse:\n\n{result.assistant_response}\n",
            encoding="utf-8",
        )
        print(json.dumps({"ok": True, "finish_reason": result.finish_reason}, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        payload = {
            "status": "fail",
            "started_at": started,
            "ended_at": datetime.now(UTC).isoformat(),
            "error": str(exc),
            "notes": "Smoke failed; do not execute full rc2 benchmark without authorization after fix.",
        }
        write_json(OUT / "smoke_result.json", payload)
        (OUT / "SMOKE.md").write_text(
            f"# RC2 readiness smoke\n\nStatus: **fail**\n\nError: {exc}\n",
            encoding="utf-8",
        )
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
