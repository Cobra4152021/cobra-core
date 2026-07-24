#!/usr/bin/env python3
"""Phase 4 full capability validation worker (46 tasks). Framework frozen. Not CobraBench."""

from __future__ import annotations

import json
import os
import re
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

import psutil
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV_HASH = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
SYSTEM = (
    "You are an evidence-first assistant. Use only supplied evidence when sources "
    "are provided. Cite source keys. Do not invent sources, APIs, or facts. "
    "When evidence is insufficient, say so and list unknowns."
)
CITE_RE = re.compile(r"\[(?:S|W|E)\d+\]|\[[A-E]\]")


def _mem() -> dict:
    vm = psutil.virtual_memory()
    return {
        "available_ram_bytes": int(vm.available),
        "total_ram_bytes": int(vm.total),
        "used_ram_bytes": int(vm.used),
    }


def extract_citations(text: str) -> list[str]:
    return sorted(set(CITE_RE.findall(text or "")))


def generate(tokenizer, model, device, prompt: str, max_new: int) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]
    try:
        rendered = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
    except TypeError:
        rendered = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    inputs = tokenizer([rendered], return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    torch.manual_seed(123)
    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new, do_sample=False)
    latency = time.perf_counter() - t0
    gen = out[0][inputs["input_ids"].shape[-1] :]
    text = tokenizer.decode(gen, skip_special_tokens=True)
    return {
        "text": text,
        "latency_s": round(latency, 3),
        "output_tokens": int(gen.shape[-1]),
        "input_tokens": int(inputs["input_ids"].shape[-1]),
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated()),
        "memory": _mem(),
        "citations": extract_citations(text),
    }


def main() -> int:
    model_dir = Path(os.environ.get("COBRA_CLOUD_MODEL_DIR", "/workspace/models/qwen3-8b"))
    inv_path = Path(
        os.environ.get("COBRA_CLOUD_INVENTORY", "/workspace/transfer/qwen3-8b-local-inventory.json")
    )
    pack_path = Path(os.environ.get("COBRA_TASKPACK", "/workspace/cobra-pilot/taskpack.json"))
    out_dir = Path(os.environ.get("COBRA_PILOT_OUT", "/workspace/phase4-out"))
    out_dir.mkdir(parents=True, exist_ok=True)

    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    if inv.get("inventory_hash") != MODEL_INV_HASH:
        raise SystemExit(f"inventory hash mismatch: {inv.get('inventory_hash')}")
    if inv.get("model_revision") != MODEL_REVISION:
        raise SystemExit("model revision mismatch")

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    tasks = pack["tasks"]
    if len(tasks) != 46:
        raise SystemExit(f"expected 46 tasks, got {len(tasks)}")

    report: dict = {
        "schema": "cobra.diagnostics.phase4_full_run.v1",
        "started_at": datetime.now(UTC).isoformat(),
        "python": __import__("sys").version,
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cuda_available": bool(torch.cuda.is_available()),
        "framework_frozen": True,
        "prompt_tuning": False,
        "benchmark_content": False,
        "task_count": len(tasks),
        "tasks": [],
    }
    if not torch.cuda.is_available():
        raise SystemExit("cuda unavailable")

    os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

    qcfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=False)
    t_load = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        str(model_dir),
        trust_remote_code=False,
        device_map={"": 0},
        low_cpu_mem_usage=True,
        quantization_config=qcfg,
    )
    model.eval()
    load_s = time.perf_counter() - t_load
    device = next(model.parameters()).device
    report["load_seconds"] = round(load_s, 3)
    report["peak_vram_after_load"] = int(torch.cuda.max_memory_allocated())
    report["memory_after_load"] = _mem()
    (out_dir / "run_partial.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for idx, task in enumerate(tasks, start=1):
        tid = task["id"]
        print(f"task_begin {idx}/46 {tid}", flush=True)
        task_dir = out_dir / "tasks" / tid
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "prompt.txt").write_text(task["prompt"], encoding="utf-8")
        repeats = int(task.get("repeats") or 1)
        max_new = int(task.get("max_new_tokens") or 512)
        outputs = []
        err = None
        try:
            for i in range(repeats):
                g = generate(tokenizer, model, device, task["prompt"], max_new)
                outputs.append(g)
                (task_dir / f"output_{i+1}.txt").write_text(g["text"], encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
            (task_dir / "error.txt").write_text(traceback.format_exc()[-4000:], encoding="utf-8")
        entry = {
            "id": tid,
            "domain": task["domain"],
            "repeats": repeats,
            "max_new_tokens": max_new,
            "success": err is None and all(bool((o.get("text") or "").strip()) for o in outputs),
            "error": err,
            "meta": task.get("meta") or {},
            "outputs": [
                {
                    "latency_s": o["latency_s"],
                    "output_tokens": o["output_tokens"],
                    "input_tokens": o["input_tokens"],
                    "peak_vram_bytes": o["peak_vram_bytes"],
                    "memory": o["memory"],
                    "char_len": len(o.get("text") or ""),
                    "citations": o.get("citations") or [],
                }
                for o in outputs
            ],
        }
        report["tasks"].append(entry)
        (task_dir / "metrics.json").write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        (out_dir / "run_partial.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"task_end {tid} success={entry['success']}", flush=True)

    report["ended_at"] = datetime.now(UTC).isoformat()
    report["peak_vram_bytes"] = int(torch.cuda.max_memory_allocated())
    report["memory_end"] = _mem()
    report["successes"] = sum(1 for t in report["tasks"] if t.get("success"))
    (out_dir / "RUN.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("phase4_tasks", len(report["tasks"]), "successes", report["successes"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
