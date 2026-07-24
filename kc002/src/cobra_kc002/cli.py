"""KC-002 CLI — real-weight gates only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import torch
from PIL import Image, ImageDraw

from cobra_kc002.cost import CostMeter
from cobra_kc002.env_gate import collect_env, require_real_weight_env, write_env_artifact
from cobra_kc002.real_model import assert_no_surrogate, load_real_stack


BASELINE_PROMPTS = [
    ("T1", 'Say the word "ok" and nothing else.'),
    ("T2", "What is 17+4? Reply with only the number."),
    ("T3", "Translate to French: good morning"),
    ("T4", "Write a JSON object with keys a=1 and b=2 only."),
    ("T5", "List three primary colors as a comma-separated list."),
]


def _art() -> Path:
    root = Path(os.environ.get("COBRA_EXPERIMENT_DIR", "artifacts/experiments"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def validate_env(_: argparse.Namespace) -> int:
    report = write_env_artifact(_art() / "env_report.json")
    print(json.dumps(report.__dict__, indent=2))
    if not report.ok:
        print("ENVIRONMENT GATE FAILED", file=sys.stderr)
        return 2
    return 0


def text_baseline(_: argparse.Namespace) -> int:
    require_real_weight_env()
    meter = CostMeter.from_env()
    model = load_real_stack(load_4bit=True, enable_lora=False)
    assert_no_surrogate(model)
    rows = []
    for pid, prompt in BASELINE_PROMPTS:
        meter.check()
        row = model.generate_text(prompt, max_new_tokens=64, seed=42)
        row2 = model.generate_text(prompt, max_new_tokens=64, seed=42)
        rows.append(
            {
                "prompt_id": pid,
                "prompt": prompt,
                "output": row["text"],
                "repeat_match": row["text"] == row2["text"],
                **{k: row[k] for k in ("input_tokens", "output_tokens", "latency_ms", "peak_vram_gb")},
            }
        )
    out = {
        "meta": model.meta.__dict__,
        "rows": rows,
        "cost": meter.__dict__,
    }
    (_art() / "real_text_baseline.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


def _synth_images() -> dict[str, Image.Image]:
    def solid(rgb, label):
        im = Image.new("RGB", (384, 384), rgb)
        d = ImageDraw.Draw(im)
        d.rectangle([64, 64, 320, 320], outline=(0, 0, 0), width=6)
        d.text((80, 180), label, fill=(0, 0, 0))
        return im

    return {
        "photo": solid((180, 120, 80), "photo"),
        "chart": solid((240, 240, 240), "chart"),
        "screenshot": solid((30, 30, 40), "ui"),
        "document": solid((255, 255, 255), "DOC"),
        "blank": Image.new("RGB", (384, 384), (0, 0, 0)),
        "noise": Image.fromarray(
            (__import__("numpy").random.default_rng(0).integers(0, 256, (384, 384, 3), dtype="uint8"))
        ),
        "wide": Image.new("RGB", (768, 192), (0, 128, 255)),
    }


def siglip(_: argparse.Namespace) -> int:
    require_real_weight_env()
    model = load_real_stack(load_4bit=True, enable_lora=False)
    assert_no_surrogate(model)
    results = []
    for name, im in _synth_images().items():
        proc = model.image_processor(images=im.convert("RGB"), return_tensors="pt")
        pv = proc["pixel_values"]
        # vision may be cpu or cuda
        device = next(model.vision_stack.vision.parameters()).device
        pv = pv.to(device)
        t0 = time.perf_counter()
        feats = model.vision_stack.forward_features(pv)
        dt = (time.perf_counter() - t0) * 1000
        results.append(
            {
                "name": name,
                "pixel_shape": list(pv.shape),
                "feature_shape": list(feats.shape),
                "dtype": str(feats.dtype),
                "device": str(feats.device),
                "finite": bool(torch.isfinite(feats).all()),
                "latency_ms": round(dt, 2),
                "image_sha256": hashlib.sha256(im.tobytes()).hexdigest(),
            }
        )
    out = {"pseudo_layers": list(model.vision_stack.layers), "images": results, "meta": model.meta.__dict__}
    (_art() / "siglip_validation.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if all(r["finite"] for r in results) else 1


def forward_gate(_: argparse.Namespace) -> int:
    """Mandatory KC-002 gate: real multimodal forward, no surrogate."""
    require_real_weight_env()
    meter = CostMeter.from_env()
    model = load_real_stack(load_4bit=True, enable_lora=False)
    assert_no_surrogate(model)
    im = _synth_images()["photo"]
    proc = model.image_processor(images=im, return_tensors="pt")
    vdevice = next(model.vision_stack.vision.parameters()).device
    pv = proc["pixel_values"].to(vdevice)
    ids = model.tokenizer("What color is the square outline near?", return_tensors="pt")
    # move ids to lm device
    lm_device = model.lm.get_input_embeddings().weight.device
    ids = {k: v.to(lm_device) for k, v in ids.items()}
    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    with torch.no_grad():
        visual = model.encode_images(pv)
        out = model(pixel_values=pv, input_ids=ids["input_ids"], attention_mask=ids.get("attention_mask"))
        logits = out.logits if hasattr(out, "logits") else out["logits"]
    dt = (time.perf_counter() - t0) * 1000
    meter.check()
    trace = {
        "used_surrogate": False,
        "gpt_oss_id": model.meta.gpt_oss_id,
        "siglip_id": model.meta.siglip_id,
        "pseudo_layers": list(model.vision_stack.layers),
        "pixel_values": list(pv.shape),
        "visual_tokens": list(visual.shape),
        "visual_dtype": str(visual.dtype),
        "visual_device": str(visual.device),
        "logits_shape": list(logits.shape),
        "logits_finite": bool(torch.isfinite(logits).all()),
        "latency_ms": round(dt, 2),
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / (1024**3), 3),
        "cost": meter.__dict__,
    }
    ok = (
        trace["logits_finite"]
        and visual.shape[-1] == 2880
        and visual.shape[1] == 729
        and not model.meta.used_surrogate
    )
    trace["ok"] = ok
    (_art() / "forward_gate.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
    print(json.dumps(trace, indent=2))
    return 0 if ok else 1


def overfit(_: argparse.Namespace) -> int:
    require_real_weight_env()
    meter = CostMeter.from_env()
    model = load_real_stack(load_4bit=True, enable_lora=True, lora_r=16, lora_alpha=32)
    assert_no_surrogate(model)
    model.train()
    # Tiny legally cleared synthetic set from data/kc002
    from cobra_kc002.dataset import load_micro_dataset

    data = load_micro_dataset(Path(__file__).resolve().parents[3] / "data" / "kc002")
    train = [x for x in data if x["split"] == "train"][:16]
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=1e-4)
    losses = []
    steps = 40
    for step in range(steps):
        meter.check()
        ex = train[step % len(train)]
        im = Image.open(ex["image_path"]).convert("RGB")
        proc = model.image_processor(images=im, return_tensors="pt")
        vdevice = next(model.vision_stack.vision.parameters()).device
        pv = proc["pixel_values"].to(vdevice)
        # Supervised: question + answer tokens; mask question
        text = ex["question"] + "\n" + ex["expected_answer"]
        toks = model.tokenizer(text, return_tensors="pt")
        lm_device = model.lm.get_input_embeddings().weight.device
        input_ids = toks["input_ids"].to(lm_device)
        labels = input_ids.clone()
        # rough mask: first half ignored
        cut = max(1, input_ids.shape[1] // 2)
        labels[:, :cut] = -100
        opt.zero_grad(set_to_none=True)
        out = model(pixel_values=pv, input_ids=input_ids, labels=labels)
        loss = out.loss if hasattr(out, "loss") else out["loss"]
        loss.backward()
        # gradient checks
        if step == 0:
            proj_g = any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.projector.parameters())
            lora_g = any(
                p.grad is not None and p.grad.abs().sum() > 0
                for n, p in model.named_parameters()
                if "lora_" in n
            )
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        losses.append(float(loss.detach()))
        meter.save(_art() / "cost_meter.json")
    result = {
        "ok": losses[-1] < losses[0] * 0.7 or losses[-1] < 2.0,
        "loss_start": losses[0],
        "loss_end": losses[-1],
        "steps": steps,
        "projector_grad": proj_g,
        "lora_grad": lora_g,
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / (1024**3), 3),
        "meta": model.meta.__dict__,
        "cost": meter.__dict__,
    }
    (_art() / "overfit_real.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] and result["projector_grad"] and result["lora_grad"] else 1


def image_dependence(_: argparse.Namespace) -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "blocked": True,
                "reason": "Run on CUDA host after overfit; see docs/KC002_IMAGE_DEPENDENCE.md",
            },
            indent=2,
        )
    )
    return 2


def text_regression(_: argparse.Namespace) -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "blocked": True,
                "reason": "Run on CUDA host after overfit; threshold 5% — docs/KC002_TEXT_REGRESSION.md",
            },
            indent=2,
        )
    )
    return 2


def moe_routing(_: argparse.Namespace) -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "blocked": True,
                "reason": "Requires real GPT-OSS router hooks on CUDA host",
            },
            indent=2,
        )
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kc002")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in (
        "validate-env",
        "text-baseline",
        "siglip",
        "forward-gate",
        "overfit",
        "image-dependence",
        "text-regression",
        "moe-routing",
    ):
        sub.add_parser(name)
    args = p.parse_args(argv)
    return {
        "validate-env": validate_env,
        "text-baseline": text_baseline,
        "siglip": siglip,
        "forward-gate": forward_gate,
        "overfit": overfit,
        "image-dependence": image_dependence,
        "text-regression": text_regression,
        "moe-routing": moe_routing,
    }[args.cmd](args)


def main_entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main())
