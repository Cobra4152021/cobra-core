"""Real GPT-OSS + SigLIP multimodal stack (no surrogate)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    SiglipImageProcessor,
    SiglipVisionModel,
)

from cobra_kc001.integration import build_prepend_sequence
from cobra_kc001.projector import ProjectorConfig, VisionProjector
from cobra_kc002 import GPT_OSS_HIDDEN, GPT_OSS_ID, IMAGE_TOKENS, PSEUDO_LAYERS, SIGLIP_ID
from cobra_kc002.env_gate import require_real_weight_env


@dataclass
class LoadMeta:
    gpt_oss_id: str
    gpt_oss_revision: str
    siglip_id: str
    siglip_revision: str
    quant: str
    dtype: str
    device_map: str
    peak_vram_gb: float | None
    used_surrogate: bool = False


def _peak_vram_gb() -> float | None:
    if not torch.cuda.is_available():
        return None
    return round(torch.cuda.max_memory_allocated() / (1024**3), 3)


class RealPseudoDeepStack(nn.Module):
    """Frozen real SigLIP with documented layer indices."""

    def __init__(self, vision: SiglipVisionModel, layers: tuple[int, ...] = PSEUDO_LAYERS) -> None:
        super().__init__()
        self.vision = vision
        self.layers = layers
        n = int(vision.config.num_hidden_layers)
        # HF hidden_states: 0=embed, 1..n = layers → index n is final
        for li in layers:
            if li < 0 or li > n:
                raise ValueError(
                    f"PseudoDeepStack layer {li} invalid for SigLIP with num_hidden_layers={n}"
                )
        self.vision.eval()
        for p in self.vision.parameters():
            p.requires_grad = False

    @torch.no_grad()
    def forward_features(self, pixel_values: torch.Tensor) -> torch.Tensor:
        out = self.vision(pixel_values=pixel_values, output_hidden_states=True)
        hs = out.hidden_states
        parts = []
        for li in self.layers:
            feat = hs[li]
            if feat.shape[1] == IMAGE_TOKENS + 1:
                feat = feat[:, 1:, :]
            if feat.shape[1] != IMAGE_TOKENS:
                raise RuntimeError(
                    f"layer {li} token count {feat.shape[1]} != expected {IMAGE_TOKENS}"
                )
            parts.append(feat)
        cat = torch.cat(parts, dim=-1)
        if not torch.isfinite(cat).all():
            raise RuntimeError("non-finite PseudoDeepStack features")
        return cat


def discover_lora_targets(model: nn.Module) -> list[str]:
    """Enumerate module names; select attention projections by substring."""
    names = [n for n, _ in model.named_modules()]
    candidates = []
    # GPT-OSS / common HF patterns — do not assume; filter by inspection.
    keys = ("q_proj", "k_proj", "v_proj", "o_proj", "qkv_proj", "out_proj", "self_attn")
    for n in names:
        leaf = n.split(".")[-1]
        if leaf in {"q_proj", "k_proj", "v_proj", "o_proj", "out_proj"}:
            candidates.append(n)
        elif leaf == "qkv_proj":
            candidates.append(n)
    # Prefer unique leaf target names for PEFT
    leaves = sorted({c.split(".")[-1] for c in candidates})
    if not leaves:
        # Fallback scan
        for n in names:
            if "self_attn" in n and n.split(".")[-1] in keys:
                leaves.append(n.split(".")[-1])
        leaves = sorted(set(leaves))
    if not leaves:
        raise RuntimeError(
            "No LoRA target modules found; inspect model.named_modules() manually"
        )
    return leaves


class RealCobraVisionLM(nn.Module):
    """Real weights only. Raises if surrogate components are requested."""

    def __init__(
        self,
        *,
        lm: nn.Module,
        tokenizer: Any,
        vision_stack: RealPseudoDeepStack,
        projector: VisionProjector,
        image_processor: Any,
        meta: LoadMeta,
        lora_enabled: bool,
    ) -> None:
        super().__init__()
        if meta.used_surrogate:
            raise RuntimeError("Surrogate models are forbidden in KC-002")
        self.lm = lm
        self.tokenizer = tokenizer
        self.vision_stack = vision_stack
        self.projector = projector
        self.image_processor = image_processor
        self.meta = meta
        self.lora_enabled = lora_enabled

    def encode_images(self, pixel_values: torch.Tensor) -> torch.Tensor:
        # Features under no_grad from frozen SigLIP; projector may train.
        with torch.no_grad():
            feats = self.vision_stack.forward_features(pixel_values)
        feats = feats.to(dtype=next(self.projector.parameters()).dtype)
        return self.projector(feats)

    def forward(
        self,
        pixel_values: torch.Tensor | None,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
    ) -> Any:
        embed = self.lm.get_input_embeddings()
        text_embeds = embed(input_ids)
        if pixel_values is None:
            return self.lm(
                inputs_embeds=text_embeds,
                attention_mask=attention_mask
                if attention_mask is not None
                else torch.ones_like(input_ids),
                labels=labels,
            )
        visual = self.encode_images(pixel_values)
        # Ensure device match with LM embeds
        visual = visual.to(device=text_embeds.device, dtype=text_embeds.dtype)
        seq = build_prepend_sequence(visual, text_embeds, labels=labels)
        return self.lm(
            inputs_embeds=seq.inputs_embeds,
            attention_mask=seq.attention_mask,
            labels=seq.labels,
        )

    @torch.no_grad()
    def generate_text(self, prompt: str, max_new_tokens: int = 64, seed: int = 42) -> dict:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        toks = self.tokenizer(prompt, return_tensors="pt")
        device = next(self.lm.parameters()).device
        toks = {k: v.to(device) for k, v in toks.items()}
        t0 = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
        t1 = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
        if t0:
            t0.record()
        out = self.lm.generate(
            **toks,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )
        if t1:
            t1.record()
            torch.cuda.synchronize()
            latency_ms = float(t0.elapsed_time(t1))
        else:
            latency_ms = None
        text = self.tokenizer.decode(out[0], skip_special_tokens=True)
        return {
            "text": text,
            "input_tokens": int(toks["input_ids"].numel()),
            "output_tokens": int(out.numel() - toks["input_ids"].numel()),
            "latency_ms": latency_ms,
            "peak_vram_gb": _peak_vram_gb(),
        }


def load_real_stack(
    *,
    load_4bit: bool = True,
    enable_lora: bool = False,
    lora_r: int = 16,
    lora_alpha: int = 32,
) -> RealCobraVisionLM:
    """Load real GPT-OSS + SigLIP + projector. Fails closed without CUDA/VRAM."""
    require_real_weight_env()
    if os.environ.get("COBRA_ALLOW_SURROGATE", "0") in {"1", "true", "yes"}:
        raise RuntimeError("Surrogate mode forbidden")

    gpt_id = os.environ.get("COBRA_GPT_OSS_ID", GPT_OSS_ID)
    gpt_rev = os.environ.get("COBRA_GPT_OSS_REVISION", "main")
    sig_id = os.environ.get("COBRA_SIGLIP_ID", SIGLIP_ID)
    sig_rev = os.environ.get("COBRA_SIGLIP_REVISION", "main")

    torch.cuda.reset_peak_memory_stats()
    tokenizer = AutoTokenizer.from_pretrained(gpt_id, revision=gpt_rev, trust_remote_code=True)

    quant = "none"
    bnb = None
    if load_4bit:
        quant = "nf4"
        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

    lm = AutoModelForCausalLM.from_pretrained(
        gpt_id,
        revision=gpt_rev,
        trust_remote_code=True,
        quantization_config=bnb,
        device_map="auto",
        torch_dtype=torch.bfloat16 if not load_4bit else None,
    )
    lm.eval()

    image_processor = SiglipImageProcessor.from_pretrained(sig_id, revision=sig_rev)
    vision = SiglipVisionModel.from_pretrained(
        sig_id, revision=sig_rev, torch_dtype=torch.float32
    )
    # Keep vision on CUDA if memory allows; else CPU offload
    try:
        vision = vision.to("cuda")
    except Exception:
        vision = vision.to("cpu")
    vision_stack = RealPseudoDeepStack(vision, PSEUDO_LAYERS)

    projector = VisionProjector(
        ProjectorConfig(in_dim=1152 * 3, hidden_dim=GPT_OSS_HIDDEN, out_dim=GPT_OSS_HIDDEN)
    ).to(dtype=torch.bfloat16)
    if torch.cuda.is_available():
        projector = projector.to("cuda")

    lora_on = False
    if enable_lora:
        targets = discover_lora_targets(lm)
        # PEFT wants short names often
        target_modules = sorted({t.split(".")[-1] for t in targets})
        cfg = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=target_modules,
        )
        lm = get_peft_model(lm, cfg)
        lora_on = True
        # Freeze base; LoRA + projector train
        for n, p in lm.named_parameters():
            if "lora_" not in n:
                p.requires_grad = False

    for p in projector.parameters():
        p.requires_grad = True

    meta = LoadMeta(
        gpt_oss_id=gpt_id,
        gpt_oss_revision=gpt_rev,
        siglip_id=sig_id,
        siglip_revision=sig_rev,
        quant=quant,
        dtype="bfloat16",
        device_map="auto",
        peak_vram_gb=_peak_vram_gb(),
        used_surrogate=False,
    )
    return RealCobraVisionLM(
        lm=lm,
        tokenizer=tokenizer,
        vision_stack=vision_stack,
        projector=projector,
        image_processor=image_processor,
        meta=meta,
        lora_enabled=lora_on,
    )


def assert_no_surrogate(model: RealCobraVisionLM) -> None:
    from cobra_kc001.tiny_lm import TinyGptOssForCausalLM

    if isinstance(model.lm, TinyGptOssForCausalLM) or (
        isinstance(model.lm, PeftModel) and isinstance(model.lm.get_base_model(), TinyGptOssForCausalLM)
    ):
        raise RuntimeError("Surrogate LM detected — KC-002 abort")
    if model.meta.used_surrogate:
        raise RuntimeError("used_surrogate flag set")
