#!/usr/bin/env python3
"""Phase 3B preflight + model inventory (no full benchmark)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.evaluation.rc2_run import (  # noqa: E402
    MANIFEST_PATH,
    build_model_inventory,
    collect_preflight,
    write_json,
)
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402


def main() -> int:
    preflight = collect_preflight()
    write_json(ROOT / "evaluations/preflight/qwen3-8b-v0.2-rc2-preflight.json", preflight)
    manifest = ModelManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.model_revision != "b968826d9c46dd6066d109eabc6255188de91218":
        print("MODEL REVISION MISMATCH", file=sys.stderr)
        return 2
    inventory = build_model_inventory(manifest)
    write_json(ROOT / "evaluations/model-inventory/qwen3-8b-local-inventory.json", inventory)
    print(
        json.dumps(
            {
                "preflight_status": preflight["pass_fail_status"],
                "warnings": preflight["warnings"],
                "model_inventory_hash": inventory["inventory_hash"],
                "file_count": len(inventory["files"]),
            },
            indent=2,
        )
    )
    return 0 if preflight["pass_fail_status"] != "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())
