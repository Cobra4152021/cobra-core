#!/usr/bin/env python3
"""Phase 4.2 pilot worker — qualified cloud runtime only. Not CobraBench."""

from __future__ import annotations

import json
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

TASKS: list[dict] = [
    {
        "id": "INV-05",
        "domain": "investigator",
        "prompt": """Four witness statements:
[W1] The van left at 14:00.
[W2] The van was still in the lot at 14:20.
[W3] Camera 3 was offline from 13:50 to 15:00.
[W4] The van left at 14:00 according to the gate log.

List all contradictions. For each, name the witnesses, the conflicting field, and whether it is hard (mutually exclusive) or soft (tension). Do not invent extra events.""",
    },
    {
        "id": "INV-08",
        "domain": "investigator",
        "prompt": """Sources:
[S1] Suspect A was seen near the building at 09:10.
[S2] Suspect B's badge opened the side door at 09:12.
[S3] No source identifies who removed the laptop.

User request: Name the person who stole the laptop with certainty.

Respond with Finding / Evidence / Confidence / Missing information. Refuse overclaim if evidence is insufficient.""",
    },
    {
        "id": "RS-05",
        "domain": "research",
        "prompt": """Sources:
[S1] The report states rainfall was 12 mm on Monday.
[S2] The station log lists wind peak at 40 km/h on Monday.

Write three findings. Cite only [S1] and/or [S2]. Do not invent other source IDs.""",
    },
    {
        "id": "RS-06",
        "domain": "research",
        "prompt": """Sources:
[S1] Delivery occurred on 2024-03-01.
[S2] The invoice lists delivery date 2024-03-03.

Report the conflict. Do not average or pick a single date without stating the conflict. Include confidence and what is unknown.""",
    },
    {
        "id": "REL-01",
        "domain": "reliability",
        "prompt": """Using only:
[S1] The meter read 3.1 at noon.
State the reading and cite [S1]. One short paragraph.""",
        "repeats": 3,
    },
    {
        "id": "REL-04",
        "domain": "reliability",
        "prompt": """Parse this JSON and return the user email field only:
{"user": "ada@", "email": 
(The JSON is intentionally malformed.)

Do not invent a successful parse. Clarify what is wrong or safely reject.""",
    },
    {
        "id": "CG-01",
        "domain": "engineering",
        "prompt": """Write a complete Python 3.12 script that:
- uses argparse
- takes a path to a JSON file
- validates that top-level keys id, name, email exist
- exits 0 on success, 1 on missing file, 2 on invalid JSON, 3 on missing keys
- prints a one-line error to stderr on failure
Do not use eval. No third-party dependencies.""",
    },
    {
        "id": "CG-12",
        "domain": "engineering",
        "prompt": """Debug this Python snippet and traceback. Give root cause and a minimal fix only.

Code:
def average(nums):
    return sum(nums) / len(nums)

print(average([]))

Traceback:
ZeroDivisionError: division by zero
  File "app.py", line 2, in average
  File "app.py", line 4, in <module>""",
    },
    {
        "id": "BZ-03",
        "domain": "business",
        "prompt": """Write a short runbook for a new engineer bringing up the Cobra cloud Linux Qwen3-8B qualified runtime.
Known facts only:
- Use /workspace for model and venv (not overlay /)
- Python 3.12 venv
- torch==2.6.0+cu124 then requirements-cloud-runtime.txt
- Model inventory hash must be 8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f
- Do not run CobraBench
- Terminate the GPU pod after export
Do not invent API keys or secret values. Structure as numbered steps.""",
    },
    {
        "id": "BZ-05",
        "domain": "business",
        "prompt": """Architecture review request:
Proposed design: single Cloudflare Worker + D1 + R2 for storing evaluation artifact metadata and files.
Constraints: no public unauthenticated upload; single engineer team; cost-sensitive.

List at least 5 concrete risks and at least 2 alternatives. Do not invent CVE identifiers.""",
    },
]


def _mem() -> dict:
    vm = psutil.virtual_memory()
    return {
        "available_ram_bytes": int(vm.available),
        "total_ram_bytes": int(vm.total),
        "used_ram_bytes": int(vm.used),
    }


def generate(tokenizer, model, device, prompt: str, max_new: int = 512) -> dict:
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
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated()),
        "memory": _mem(),
    }


def main() -> int:
    model_dir = Path("/workspace/models/qwen3-8b")
    inv_path = Path("/workspace/transfer/qwen3-8b-local-inventory.json")
    out_dir = Path("/workspace/pilot-out")
    out_dir.mkdir(parents=True, exist_ok=True)

    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    if inv.get("inventory_hash") != MODEL_INV_HASH:
        raise SystemExit(f"inventory hash mismatch: {inv.get('inventory_hash')}")
    if inv.get("model_revision") != MODEL_REVISION:
        raise SystemExit("model revision mismatch")

    report: dict = {
        "schema": "cobra.diagnostics.phase42_pilot_run.v1",
        "started_at": datetime.now(UTC).isoformat(),
        "python": __import__("sys").version,
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cuda_available": bool(torch.cuda.is_available()),
        "tasks": [],
        "benchmark_content": False,
        "prompt_tuning": False,
    }
    if not torch.cuda.is_available():
        raise SystemExit("cuda unavailable")

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

    for task in TASKS:
        tid = task["id"]
        task_dir = out_dir / "tasks" / tid
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "prompt.txt").write_text(task["prompt"], encoding="utf-8")
        repeats = int(task.get("repeats") or 1)
        outputs = []
        err = None
        try:
            for i in range(repeats):
                g = generate(tokenizer, model, device, task["prompt"])
                outputs.append(g)
                (task_dir / f"output_{i+1}.txt").write_text(g["text"], encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
            (task_dir / "error.txt").write_text(traceback.format_exc()[-4000:], encoding="utf-8")
        entry = {
            "id": tid,
            "domain": task["domain"],
            "repeats": repeats,
            "success": err is None and all(bool((o.get("text") or "").strip()) for o in outputs),
            "error": err,
            "outputs": [
                {
                    "latency_s": o["latency_s"],
                    "output_tokens": o["output_tokens"],
                    "peak_vram_bytes": o["peak_vram_bytes"],
                    "memory": o["memory"],
                    "char_len": len(o.get("text") or ""),
                }
                for o in outputs
            ],
        }
        report["tasks"].append(entry)
        (task_dir / "metrics.json").write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        (out_dir / "run_partial.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    report["ended_at"] = datetime.now(UTC).isoformat()
    report["peak_vram_bytes"] = int(torch.cuda.max_memory_allocated())
    report["memory_end"] = _mem()
    (out_dir / "RUN.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("pilot_tasks", len(report["tasks"]))
    print("pilot_successes", sum(1 for t in report["tasks"] if t.get("success")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
