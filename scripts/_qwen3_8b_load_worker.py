#!/usr/bin/env python3
"""Child-process worker for Qwen3-8B load isolation (Phase 3C).

Invoked only by scripts/diagnose_qwen3_8b_load.py. Not part of the quality suite.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.diagnostics.load_isolation import (  # noqa: E402
    CONFIGS,
    MANIFEST_PATH,
    MODEL_REVISION,
    SMOKE_PROMPT,
    system_memory,
    write_json,
)
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402


def _progress(path: Path, stage: str, detail: str = "") -> None:
    payload = {
        "ts": datetime.now(UTC).isoformat(),
        "stage": stage,
        "detail": detail,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
        fh.flush()


def _metadata_scan(artifact_dir: Path, progress: Path) -> dict:
    from safetensors import safe_open

    _progress(progress, "metadata_begin")
    index_path = artifact_dir / "model.safetensors.index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    weight_map = index.get("weight_map", {})
    shards = sorted(set(weight_map.values()))
    opened = []
    for shard in shards:
        p = artifact_dir / shard
        _progress(progress, "safetensors_open", shard)
        with safe_open(str(p), framework="pt", device="cpu") as f:
            keys = list(f.keys())[:3]
            opened.append({"shard": shard, "size_bytes": p.stat().st_size, "sample_keys": keys})
    tok_files = ["tokenizer.json", "tokenizer_config.json", "config.json"]
    for name in tok_files:
        assert (artifact_dir / name).is_file(), name
    _progress(progress, "metadata_complete", f"shards={len(shards)}")
    return {"shards_opened": opened, "index_weight_entries": len(weight_map)}


def _load_model(cfg: dict, artifact_dir: Path, progress: Path) -> object:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    _progress(progress, "tokenizer_begin")
    tokenizer = AutoTokenizer.from_pretrained(str(artifact_dir), trust_remote_code=False)
    _progress(progress, "tokenizer_complete")

    quant = cfg["quantization"]
    load_kwargs: dict = {
        "trust_remote_code": False,
        "low_cpu_mem_usage": bool(cfg.get("low_cpu_mem_usage", True)),
    }
    device_map = cfg.get("device_map")
    if device_map is not None:
        load_kwargs["device_map"] = device_map
    if cfg.get("max_memory") is not None:
        load_kwargs["max_memory"] = cfg["max_memory"]
    if cfg.get("offload_state_dict"):
        offload = artifact_dir.parent / "offload-cache-diag"
        offload.mkdir(parents=True, exist_ok=True)
        load_kwargs["offload_folder"] = str(offload)
        load_kwargs["offload_state_dict"] = True

    if quant == "4bit-nf4-double":
        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
    elif quant == "8bit":
        load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
    else:
        raise ValueError(f"unsupported quant {quant}")

    _progress(
        progress,
        "model_from_pretrained_begin",
        json.dumps({k: str(v) for k, v in load_kwargs.items() if k != "quantization_config"}),
    )
    t0 = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(str(artifact_dir), **load_kwargs)
    model.eval()
    _progress(progress, "model_from_pretrained_complete", f"seconds={time.perf_counter() - t0:.2f}")
    return tokenizer, model


def _generate(tokenizer: object, model: object, progress: Path, max_new: int) -> dict:
    import torch

    _progress(progress, "generate_begin")
    messages = [
        {"role": "system", "content": "Use only supplied evidence. Cite source keys."},
        {"role": "user", "content": SMOKE_PROMPT},
    ]
    rendered = tokenizer.apply_chat_template(  # type: ignore[attr-defined]
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tokenizer([rendered], return_tensors="pt")  # type: ignore[operator]
    # Place inputs on first parameter device
    device = next(model.parameters()).device  # type: ignore[attr-defined]
    inputs = {k: v.to(device) for k, v in inputs.items()}
    torch.manual_seed(123)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(  # type: ignore[attr-defined]
            **inputs,
            max_new_tokens=max_new,
            do_sample=False,
        )
    gen = out[0][inputs["input_ids"].shape[-1] :]
    text = tokenizer.decode(gen, skip_special_tokens=True)  # type: ignore[attr-defined]
    peak = None
    if torch.cuda.is_available():
        peak = int(torch.cuda.max_memory_allocated())
    _progress(progress, "generate_complete", f"chars={len(text)}")
    return {
        "text": text,
        "output_tokens": int(gen.shape[-1]),
        "latency_s": round(time.perf_counter() - t0, 3),
        "peak_vram_bytes": peak,
        "non_empty": bool(text.strip()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-id", required=True)
    parser.add_argument("--result-json", required=True, type=Path)
    parser.add_argument("--progress-jsonl", required=True, type=Path)
    args = parser.parse_args()
    cfg = CONFIGS[args.config_id]
    progress = args.progress_jsonl
    progress.parent.mkdir(parents=True, exist_ok=True)
    progress.write_text("", encoding="utf-8")

    started = datetime.now(UTC).isoformat()
    result: dict = {
        "configuration_id": args.config_id,
        "config": cfg,
        "started_at": started,
        "success": False,
        "load_stage": "init",
        "error": None,
        "generation": None,
        "memory_before": system_memory(),
        "prompt_is_benchmark": False,
        "smoke_prompt_fingerprint": "synthetic-src-abc-v1",
    }
    write_json(args.result_json, result)

    try:
        manifest = ModelManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))
        if manifest.model_revision != MODEL_REVISION:
            raise RuntimeError(f"revision mismatch: {manifest.model_revision}")
        artifact = Path(manifest.local_artifact_root or "")
        if not artifact.is_dir():
            raise RuntimeError(f"missing artifacts: {artifact}")
        result["artifact_root"] = str(artifact)
        result["model_revision"] = manifest.model_revision

        if cfg.get("metadata_only"):
            result["load_stage"] = "metadata"
            result["metadata"] = _metadata_scan(artifact, progress)
            result["success"] = True
            result["load_stage"] = "metadata_complete"
        else:
            result["load_stage"] = "loading"
            write_json(args.result_json, result)
            tokenizer, model = _load_model(cfg, artifact, progress)
            result["load_stage"] = "loaded"
            result["success"] = True
            if cfg.get("generate"):
                result["generation"] = _generate(
                    tokenizer, model, progress, int(cfg.get("max_new_tokens", 64))
                )
                result["success"] = bool(result["generation"].get("non_empty"))
                result["load_stage"] = "generated" if result["success"] else "generate_empty"
            # Explicit cleanup before exit
            del model
            del tokenizer
            try:
                import gc

                import torch

                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:  # noqa: BLE001
                pass
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        result["traceback"] = traceback.format_exc()
        result["success"] = False
        _progress(progress, "exception", str(exc))

    result["ended_at"] = datetime.now(UTC).isoformat()
    result["memory_after"] = system_memory()
    write_json(args.result_json, result)
    return 0 if result.get("success") else 2


if __name__ == "__main__":
    raise SystemExit(main())
