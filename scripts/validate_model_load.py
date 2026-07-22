#!/usr/bin/env python3
"""Minimal load + inference validation before CobraBench (no full smoke suite)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.inference.engine import LocalInferenceEngine  # noqa: E402
from cobra_core.providers.qwen_local import QwenLocalAdapter  # noqa: E402
from cobra_core.schemas.inference import InferenceRequest  # noqa: E402
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=32)
    args = parser.parse_args(argv)

    manifest = ModelManifest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
    adapter = QwenLocalAdapter(load_in_4bit=True, max_memory={0: "9GiB", "cpu": "18GiB"})
    engine = LocalInferenceEngine(adapter)
    report: dict[str, object] = {
        "model_name": manifest.model_name,
        "model_revision": manifest.model_revision,
        "steps": {},
    }

    try:
        # Exact-response technical check
        exact = engine.run(
            manifest=manifest,
            manifest_ref=str(args.manifest),
            request=InferenceRequest(
                system_prompt="Follow instructions exactly.",
                user_prompt="Reply with exactly: COBRA_MODEL_OK",
                temperature=0.0,
                seed=123,
                max_new_tokens=args.max_new_tokens,
                enable_thinking=False,
            ),
            persist=False,
        )
        exact_ok = exact.assistant_response.strip() == "COBRA_MODEL_OK"
        report["steps"]["exact_response"] = {
            "ok": exact_ok,
            "response": exact.assistant_response[:200],
            "latency_ms": exact.total_latency_ms,
            "output_tokens": exact.output_token_count,
            "warnings": exact.warnings,
        }

        grounded = engine.run(
            manifest=manifest,
            manifest_ref=str(args.manifest),
            request=InferenceRequest(
                system_prompt="Use only the passage. If unknown, say UNKNOWN.",
                user_prompt=(
                    "Passage: Crate SK-42 is sealed in Bay 7.\n"
                    "Question: Where is SK-42? Answer briefly."
                ),
                temperature=0.0,
                seed=123,
                max_new_tokens=64,
                enable_thinking=False,
            ),
            persist=False,
        )
        grounded_text = grounded.assistant_response.lower()
        grounded_ok = "bay 7" in grounded_text and "sk-42" in grounded_text
        report["steps"]["grounded_passage"] = {
            "ok": grounded_ok,
            "response": grounded.assistant_response[:300],
            "latency_ms": grounded.total_latency_ms,
            "output_tokens": grounded.output_token_count,
        }

        adapter.unload()
        report["steps"]["unload"] = {"ok": True}
        report["passed"] = bool(exact_ok and grounded_ok)
    except Exception as exc:
        adapter.unload()
        report["passed"] = False
        report["error"] = str(exc)
        print(json.dumps(report, indent=2))
        return 1

    print(json.dumps(report, indent=2))
    return 0 if report.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
