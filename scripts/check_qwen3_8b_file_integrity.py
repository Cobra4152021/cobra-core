#!/usr/bin/env python3
"""Validate local Qwen3-8B artifacts without redownload (Phase 3C)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.diagnostics.load_isolation import (  # noqa: E402
    MANIFEST_PATH,
    PHASE3B_INVENTORY,
    write_json,
)
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402

OUT = ROOT / "evaluations/model-inventory/qwen3-8b-file-integrity.json"


def main() -> int:
    manifest = ModelManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))
    inv = json.loads(PHASE3B_INVENTORY.read_text(encoding="utf-8"))
    artifact = Path(manifest.local_artifact_root or "")
    issues: list[str] = []
    files_out: list[dict] = []

    if not artifact.is_dir():
        write_json(OUT, {"status": "fail", "error": "artifact root missing"})
        return 2

    inv_by_name = {f["relpath"]: f for f in inv.get("files", [])}
    index_path = artifact / "model.safetensors.index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    weight_map = index.get("weight_map", {})
    shards = sorted(set(weight_map.values()))

    for name in shards + [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "model.safetensors.index.json",
        "vocab.json",
        "merges.txt",
    ]:
        path = artifact / name
        if not path.is_file():
            issues.append(f"missing:{name}")
            continue
        size = path.stat().st_size
        if size == 0:
            issues.append(f"zero_length:{name}")
        expected = inv_by_name.get(name)
        entry = {
            "relpath": name,
            "size_bytes": size,
            "phase3b_inventory_sha256": expected["sha256"] if expected else None,
            "size_matches_inventory": bool(expected and expected["size_bytes"] == size),
        }
        if expected and expected["size_bytes"] != size:
            issues.append(f"size_mismatch:{name}")
        # Open safetensors headers for weight shards
        if name.endswith(".safetensors"):
            try:
                from safetensors import safe_open

                with safe_open(str(path), framework="pt", device="cpu") as f:
                    entry["safetensors_open_ok"] = True
                    entry["key_count"] = len(f.keys())
            except Exception as exc:  # noqa: BLE001
                entry["safetensors_open_ok"] = False
                entry["safetensors_error"] = str(exc)
                issues.append(f"safetensors_open_failed:{name}")
        files_out.append(entry)

    # Spot-hash small config only (avoid multi-GB rehash unless mismatch)
    config = artifact / "config.json"
    config_hash = hashlib.sha256(config.read_bytes()).hexdigest()
    if config_hash != inv.get("config_hash"):
        issues.append("config_hash_mismatch")

    for shard in shards:
        if shard not in {Path(p).name for p in shards}:
            pass
        if not (artifact / shard).is_file():
            issues.append(f"index_missing_shard:{shard}")

    status = "pass" if not issues else "fail"
    payload = {
        "status": status,
        "model_revision": manifest.model_revision,
        "artifact_root_sanitized": str(artifact).replace("\\", "/"),
        "phase3b_inventory_hash": inv.get("inventory_hash"),
        "config_hash": config_hash,
        "shard_count": len(shards),
        "index_weight_entries": len(weight_map),
        "files": files_out,
        "issues": issues,
        "hash_policy": "sizes compared to Phase 3B inventory; full shard rehash skipped when sizes match",
        "corruption_detected": status == "fail"
        and any("safetensors" in i or "zero" in i for i in issues),
    }
    write_json(OUT, payload)
    print(json.dumps({"status": status, "issues": issues}, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
