#!/usr/bin/env python3
"""Linux child worker for Phase 3F cloud Qwen3-8B runtime qualification."""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV_HASH = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
# Phase 3F synthetic smoke — not from CobraBench.
SMOKE_PROMPT = (
    "[S1] The shipment was logged at 08:40.\n"
    "[S2] The inspection form was signed at 09:05.\n"
    "[S3] No record identifies who moved the shipment.\n"
    "List the supported facts, identify the unresolved uncertainty, cite only S1/S2/S3."
)


def _progress(path: Path, stage: str, detail: str = "") -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps({"ts": datetime.now(UTC).isoformat(), "stage": stage, "detail": detail})
            + "\n"
        )
        fh.flush()


def _mem() -> dict:
    import psutil

    vm = psutil.virtual_memory()
    return {"available_ram_bytes": int(vm.available), "total_ram_bytes": int(vm.total)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["load", "generate", "extended"], required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--result-json", required=True, type=Path)
    parser.add_argument("--progress-jsonl", required=True, type=Path)
    parser.add_argument("--inventory-json", required=True, type=Path)
    parser.add_argument("--smoke-output", type=Path, default=None)
    args = parser.parse_args()

    progress = args.progress_jsonl
    progress.parent.mkdir(parents=True, exist_ok=True)
    progress.write_text("", encoding="utf-8")

    result: dict = {
        "mode": args.mode,
        "started_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "executable": sys.executable,
        "success": False,
        "load_stage": "init",
        "offload_used": False,
        "error": None,
        "benchmark_content": False,
        "platform": sys.platform,
    }
    args.result_json.parent.mkdir(parents=True, exist_ok=True)
    args.result_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    try:
        inv = json.loads(args.inventory_json.read_text(encoding="utf-8"))
        if inv.get("inventory_hash") != MODEL_INV_HASH:
            raise RuntimeError(f"inventory hash mismatch: {inv.get('inventory_hash')}")
        if inv.get("model_revision") != MODEL_REVISION:
            raise RuntimeError("model revision mismatch")
        artifact = Path(args.artifact_dir)
        if not artifact.is_dir():
            raise RuntimeError(f"missing artifact dir {artifact}")

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        if not torch.cuda.is_available():
            raise RuntimeError("cuda unavailable")

        result["memory_before"] = _mem()
        free, total = torch.cuda.mem_get_info()
        result["vram_before"] = {"free": int(free), "total": int(total)}
        result["gpu_name"] = torch.cuda.get_device_name(0)
        _progress(progress, "tokenizer_begin")
        tokenizer = AutoTokenizer.from_pretrained(str(artifact), trust_remote_code=False)
        _progress(progress, "tokenizer_complete")

        qcfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        load_kwargs = {
            "trust_remote_code": False,
            "device_map": {"": 0},
            "low_cpu_mem_usage": True,
            "quantization_config": qcfg,
        }
        result["configuration"] = {
            "device_map": {"": 0},
            "quantization": "4bit-nf4-double",
            "compute_dtype": "float16",
            "offload": False,
            "trust_remote_code": False,
        }
        _progress(progress, "model_load_begin", json.dumps({"device_map": {"": 0}}))
        t0 = time.perf_counter()
        model = AutoModelForCausalLM.from_pretrained(str(artifact), **load_kwargs)
        model.eval()
        load_s = time.perf_counter() - t0
        _progress(progress, "model_load_complete", f"seconds={load_s:.2f}")
        first_param = next(model.parameters())
        result["param_device"] = str(first_param.device)
        if "cpu" in str(first_param.device).lower():
            raise RuntimeError("unexpected CPU placement; offload not allowed")
        result["load_seconds"] = round(load_s, 3)
        result["load_stage"] = "loaded"
        result["success"] = True

        def generate_once(
            prompt: str,
            label: str,
            *,
            tok: object = tokenizer,
            mdl: object = model,
            device: object = first_param.device,
        ) -> dict:
            _progress(progress, f"generate_begin:{label}")
            messages = [
                {"role": "system", "content": "Use only supplied evidence. Cite source keys."},
                {"role": "user", "content": prompt},
            ]
            try:
                rendered = tok.apply_chat_template(  # type: ignore[attr-defined]
                    messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
                )
            except TypeError:
                rendered = tok.apply_chat_template(  # type: ignore[attr-defined]
                    messages, tokenize=False, add_generation_prompt=True
                )
            inputs = tok([rendered], return_tensors="pt")  # type: ignore[operator]
            inputs = {k: v.to(device) for k, v in inputs.items()}
            torch.manual_seed(123)
            g0 = time.perf_counter()
            with torch.no_grad():
                out = mdl.generate(**inputs, max_new_tokens=80, do_sample=False)  # type: ignore[attr-defined]
            gen = out[0][inputs["input_ids"].shape[-1] :]
            text = tok.decode(gen, skip_special_tokens=True)  # type: ignore[attr-defined]
            peak = int(torch.cuda.max_memory_allocated())
            _progress(progress, f"generate_complete:{label}", f"chars={len(text)}")
            return {
                "text": text,
                "non_empty": bool(text.strip()),
                "output_tokens": int(gen.shape[-1]),
                "latency_s": round(time.perf_counter() - g0, 3),
                "peak_vram_bytes": peak,
            }

        if args.mode in {"generate", "extended"}:
            gen = generate_once(SMOKE_PROMPT, "main")
            result["generation"] = gen
            result["success"] = bool(gen.get("non_empty"))
            result["load_stage"] = "generated" if result["success"] else "generate_empty"
            if args.smoke_output is not None:
                args.smoke_output.write_text(gen.get("text") or "", encoding="utf-8")

        if args.mode == "extended" and result["success"]:
            prompts = [
                SMOKE_PROMPT,
                "Using only [S1] The meter read 3.1 at noon. State the reading and cite [S1].",
                "Using only [S2] Rain began at 16:00. One sentence with citation.",
                "Using only [S3] The log omits humidity. Name the uncertainty and cite [S3].",
                "Using only [S1] A crate arrived Monday and [S2] inspection was Tuesday. "
                "State both facts with citations and one uncertainty.",
            ]
            ext = []
            for i, prompt in enumerate(prompts, start=1):
                torch.cuda.reset_peak_memory_stats()
                g = generate_once(prompt, f"ext{i}")
                ext.append({"index": i, **g, "memory": _mem()})
                if not g.get("non_empty"):
                    result["success"] = False
                    result["load_stage"] = f"extended_empty_{i}"
                    break
            result["extended"] = ext
            if result["success"]:
                result["load_stage"] = "extended_complete"

        result["memory_after"] = _mem()
        result["peak_vram_bytes"] = int(torch.cuda.max_memory_allocated())
        del model
        del tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        result["ended_at"] = datetime.now(UTC).isoformat()
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()[-4000:]
        result["ended_at"] = datetime.now(UTC).isoformat()
        _progress(progress, "error", result["error"])
        args.result_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return 1

    args.result_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
