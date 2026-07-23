"""KC-001 CLI entrypoints."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

import torch

from cobra_kc001 import __version__
from cobra_kc001.multimodal import CobraTinyVisionLM
from cobra_kc001.synthetic import (
    COLORS,
    build_color_dataset,
    make_blank,
    make_noise,
    make_solid_image,
    pil_to_tensor,
)
from cobra_kc001.tiny_lm import TinyGptOssConfig


def _device() -> torch.device:
    pref = os.environ.get("COBRA_DEVICE", "cuda")
    if pref == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def validate_env(_: argparse.Namespace | None = None) -> int:
    info = {
        "cobra_kc001_version": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": getattr(torch.version, "cuda", None),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "gpu_vram_gb": (
            round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
            if torch.cuda.is_available()
            else None
        ),
        "transformers": _pkg_ver("transformers"),
        "accelerate": _pkg_ver("accelerate"),
        "peft": _pkg_ver("peft"),
        "bitsandbytes": _pkg_ver("bitsandbytes"),
        "flash_attn": _pkg_ver("flash_attn"),
        "note": "Full GPT-OSS-20B MXFP4 typically needs >=16GB; this host may use tiny surrogate for proofs.",
    }
    print(json.dumps(info, indent=2))
    return 0


def _pkg_ver(name: str) -> str | None:
    try:
        mod = __import__(name)
        return getattr(mod, "__version__", "present")
    except Exception:
        return None


def smoke_text(_: argparse.Namespace | None = None) -> int:
    """Baseline text path on tiny GPT-OSS-shaped LM; optional HF config fetch."""
    seed = int(os.environ.get("COBRA_SEED", "42"))
    torch.manual_seed(seed)
    device = _device()
    cfg = TinyGptOssConfig()
    model = TinyGptOssForCausalLM_safe(cfg).to(device)
    ids = torch.tensor([[1, 2, 3, 4]], device=device)
    t0 = time.perf_counter()
    with torch.no_grad():
        out1 = model(input_ids=ids)
        out2 = model(input_ids=ids)
    dt = (time.perf_counter() - t0) * 1000
    same = torch.allclose(out1["logits"], out2["logits"])
    mem = None
    if device.type == "cuda":
        mem = round(torch.cuda.max_memory_allocated() / (1024**2), 2)
    print(
        json.dumps(
            {
                "ok": True,
                "deterministic": same,
                "logits_shape": list(out1["logits"].shape),
                "latency_ms_two_forwards": round(dt, 2),
                "peak_vram_mb": mem,
                "mode": "tiny_surrogate",
                "gpt_oss_config_ref": "openai/gpt-oss-20b config.json (hidden=2880, layers=24, experts=32/4)",
            },
            indent=2,
        )
    )
    # Optional: fetch real config if network available (no weights).
    try:
        from transformers import AutoConfig

        remote = os.environ.get("COBRA_GPT_OSS_PATH", "openai/gpt-oss-20b")
        conf = AutoConfig.from_pretrained(remote, trust_remote_code=True)
        print(
            json.dumps(
                {
                    "remote_config_ok": True,
                    "model_type": getattr(conf, "model_type", None),
                    "hidden_size": getattr(conf, "hidden_size", None),
                    "num_hidden_layers": getattr(conf, "num_hidden_layers", None),
                    "num_local_experts": getattr(conf, "num_local_experts", None),
                    "vocab_size": getattr(conf, "vocab_size", None),
                },
                indent=2,
            )
        )
    except Exception as exc:
        print(json.dumps({"remote_config_ok": False, "error": str(exc)}, indent=2))
    return 0


def TinyGptOssForCausalLM_safe(cfg):
    from cobra_kc001.tiny_lm import TinyGptOssForCausalLM

    return TinyGptOssForCausalLM(cfg)


def smoke_vision(_: argparse.Namespace | None = None) -> int:
    torch.manual_seed(int(os.environ.get("COBRA_SEED", "42")))
    device = _device()
    model = CobraTinyVisionLM().to(device)
    pix = pil_to_tensor(make_solid_image("red", size=112)).unsqueeze(0).to(device)
    ids = torch.tensor([[10, 11, 12]], device=device)
    t0 = time.perf_counter()
    with torch.no_grad():
        visual = model.encode_images(pix)
        out = model(pixel_values=pix, input_ids=ids)
    dt = (time.perf_counter() - t0) * 1000
    print(
        json.dumps(
            {
                "ok": True,
                "visual_tokens_shape": list(visual.shape),
                "logits_shape": list(out["logits"].shape),
                "finite": bool(torch.isfinite(visual).all() and torch.isfinite(out["logits"]).all()),
                "latency_ms": round(dt, 2),
                "native_path": "pixels→stub/SigLIP features→projector→inputs_embeds→MoE LM",
            },
            indent=2,
        )
    )
    return 0


def overfit(_: argparse.Namespace | None = None) -> int:
    torch.manual_seed(int(os.environ.get("COBRA_SEED", "42")))
    device = _device()
    model = CobraTinyVisionLM(train_mode="B").to(device)
    data = build_color_dataset(n=16)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=3e-3)
    losses = []
    steps = 80
    t0 = time.perf_counter()
    model.train()
    for step in range(steps):
        pix, ids, labels = data[step % len(data)]
        pix, ids, labels = pix.to(device), ids.to(device), labels.to(device)
        opt.zero_grad(set_to_none=True)
        out = model(pixel_values=pix, input_ids=ids, labels=labels)
        loss = out["loss"]
        assert loss is not None
        loss.backward()
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
        opt.step()
        losses.append(float(loss.detach()))
    dur = time.perf_counter() - t0
    # Accuracy: argmax at answer position under correct image
    model.eval()
    correct = 0
    with torch.no_grad():
        for pix, ids, labels in data:
            pix, ids = pix.to(device), ids.to(device)
            # Use question-only prefix for prediction
            q = ids[:, :3]
            out = model(pixel_values=pix, input_ids=q)
            # Logits at last text position after image prepend: index = t_img + 2
            t_img = model.encoder.spec.image_tokens
            pred = int(out["logits"][0, t_img + 2].argmax())
            target = int(labels[0, -1])
            correct += int(pred == target)
    art = Path(os.environ.get("COBRA_EXPERIMENT_DIR", "./artifacts/experiments"))
    art.mkdir(parents=True, exist_ok=True)
    result = {
        "ok": losses[-1] < losses[0] * 0.5 or losses[-1] < 1.0,
        "steps": steps,
        "loss_start": losses[0],
        "loss_end": losses[-1],
        "train_acc": correct / len(data),
        "duration_s": round(dur, 2),
        "trainable_map": model.trainable_map().__dict__,
        "device": str(device),
    }
    (art / "overfit_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] and result["train_acc"] >= 0.75 else 1


def image_dependence(_: argparse.Namespace | None = None) -> int:
    """Train briefly then compare correct/wrong/blank/noise/none."""
    torch.manual_seed(int(os.environ.get("COBRA_SEED", "42")))
    device = _device()
    model = CobraTinyVisionLM(train_mode="B").to(device)
    data = build_color_dataset(n=16)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=3e-3)
    model.train()
    for step in range(100):
        pix, ids, labels = data[step % len(data)]
        out = model(pixel_values=pix.to(device), input_ids=ids.to(device), labels=labels.to(device))
        opt.zero_grad(set_to_none=True)
        out["loss"].backward()
        opt.step()
    model.eval()
    # Evaluate red example
    target = 20  # red
    q = torch.tensor([[10, 11, 12]], device=device)
    conditions = {
        "correct": pil_to_tensor(make_solid_image("red", size=112)).unsqueeze(0).to(device),
        "wrong": pil_to_tensor(make_solid_image("blue", size=112)).unsqueeze(0).to(device),
        "blank": pil_to_tensor(make_blank(size=112)).unsqueeze(0).to(device),
        "noise": pil_to_tensor(make_noise(size=112, seed=1)).unsqueeze(0).to(device),
        "none": None,
    }
    t_img = model.encoder.spec.image_tokens
    rows = {}
    with torch.no_grad():
        for name, pix in conditions.items():
            out = model(pixel_values=pix, input_ids=q)
            idx = (0 if pix is None else t_img) + 2
            logits = out["logits"][0, idx]
            pred = int(logits.argmax())
            logp = float(torch.log_softmax(logits, dim=-1)[target])
            rows[name] = {"pred": pred, "logp_target": logp, "match_target": pred == target}
    # Material difference: correct logp should beat wrong/blank/none
    ok = (
        rows["correct"]["match_target"]
        and rows["correct"]["logp_target"] > rows["wrong"]["logp_target"] + 0.05
        and rows["correct"]["logp_target"] > rows["blank"]["logp_target"] + 0.05
    )
    result = {"ok": ok, "conditions": rows, "target_token": target, "colors": list(COLORS)}
    art = Path(os.environ.get("COBRA_EXPERIMENT_DIR", "./artifacts/experiments"))
    art.mkdir(parents=True, exist_ok=True)
    (art / "image_dependence_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cobra-kc001")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate-env")
    sub.add_parser("smoke-text")
    sub.add_parser("smoke-vision")
    sub.add_parser("overfit")
    sub.add_parser("image-dependence")
    args = p.parse_args(argv)
    return {
        "validate-env": validate_env,
        "smoke-text": smoke_text,
        "smoke-vision": smoke_vision,
        "overfit": overfit,
        "image-dependence": image_dependence,
    }[args.cmd](args)


# setuptools script hooks
def validate_env_entry() -> None:
    raise SystemExit(validate_env())


def smoke_text_entry() -> None:
    raise SystemExit(smoke_text())


def smoke_vision_entry() -> None:
    raise SystemExit(smoke_vision())


if __name__ == "__main__":
    raise SystemExit(main())
