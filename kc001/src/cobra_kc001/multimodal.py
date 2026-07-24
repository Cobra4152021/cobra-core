"""End-to-end tiny multimodal model for overfit / image-dependence proofs."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn

from cobra_kc001.encoder import EncoderSpec, PseudoDeepStackEncoder
from cobra_kc001.integration import EmbeddingInjector, build_prepend_sequence
from cobra_kc001.projector import ProjectorConfig, VisionProjector
from cobra_kc001.tiny_lm import TinyGptOssConfig, TinyGptOssForCausalLM


@dataclass
class TrainableMap:
    total: int
    trainable: int
    by_group: dict[str, dict[str, int]]

    @property
    def trainable_pct(self) -> float:
        return 100.0 * self.trainable / max(1, self.total)


class CobraTinyVisionLM(nn.Module):
    """Stub encoder + projector + Tiny GPT-OSS MoE.

    Proves: pixels → features → GPT-OSS-compatible embeds → LM logits / loss.
    """

    def __init__(
        self,
        *,
        lm_cfg: TinyGptOssConfig | None = None,
        vision_hidden: int = 1152,
        train_mode: str = "projector_lora_attn",
    ) -> None:
        super().__init__()
        self.lm_cfg = lm_cfg or TinyGptOssConfig()
        # Match projector dims to tiny LM, not full 2880, for local GPU proofs.
        # Surrogate uses 8x8=64 visual tokens (not SigLIP's 729) for tractable overfit.
        in_dim = vision_hidden * 3
        tiny_spec = EncoderSpec(image_size=112, patch_size=14, hidden_size=vision_hidden)
        self.encoder = PseudoDeepStackEncoder(stub=True, stub_dim=vision_hidden, spec=tiny_spec)
        self.projector = VisionProjector(
            ProjectorConfig(in_dim=in_dim, hidden_dim=self.lm_cfg.hidden_size, out_dim=self.lm_cfg.hidden_size)
        )
        self.lm = TinyGptOssForCausalLM(self.lm_cfg)
        self.injector = EmbeddingInjector(self.lm.get_input_embeddings())
        self.train_mode = train_mode
        self.apply_train_mode(train_mode)

    def apply_train_mode(self, mode: str) -> None:
        for p in self.parameters():
            p.requires_grad = False
        if mode in {"projector_only", "A"}:
            for p in self.projector.parameters():
                p.requires_grad = True
        elif mode in {"projector_lora_attn", "B"}:
            for p in self.projector.parameters():
                p.requires_grad = True
            for layer in self.lm.layers:
                for p in layer.attn.parameters():
                    p.requires_grad = True
        elif mode in {"projector_lora_router", "C"}:
            for p in self.projector.parameters():
                p.requires_grad = True
            for layer in self.lm.layers:
                for p in layer.attn.parameters():
                    p.requires_grad = True
                for p in layer.mlp.router.parameters():
                    p.requires_grad = True
        elif mode in {"broader_sft", "D"}:
            for p in self.parameters():
                p.requires_grad = True
            for p in self.encoder.parameters():
                p.requires_grad = False
        else:
            raise ValueError(mode)
        self.train_mode = mode

    def trainable_map(self) -> TrainableMap:
        groups = {
            "encoder": self.encoder,
            "projector": self.projector,
            "embed_tokens": self.lm.embed_tokens,
            "attention": nn.ModuleList([b.attn for b in self.lm.layers]),
            "mlp_experts": nn.ModuleList([b.mlp.experts for b in self.lm.layers]),
            "router": nn.ModuleList([b.mlp.router for b in self.lm.layers]),
            "norm": nn.ModuleList([b.norm1 for b in self.lm.layers] + [b.norm2 for b in self.lm.layers] + [self.lm.norm]),
            "lm_head": self.lm.lm_head,
        }
        by_group: dict[str, dict[str, int]] = {}
        total = trainable = 0
        for name, mod in groups.items():
            t = sum(p.numel() for p in mod.parameters())
            tr = sum(p.numel() for p in mod.parameters() if p.requires_grad)
            by_group[name] = {"total": t, "trainable": tr}
            total += t
            trainable += tr
        return TrainableMap(total=total, trainable=trainable, by_group=by_group)

    def encode_images(self, pixel_values: torch.Tensor) -> torch.Tensor:
        feats = self.encoder.forward_features(pixel_values)
        return self.projector(feats)

    def forward(
        self,
        pixel_values: torch.Tensor | None,
        input_ids: torch.Tensor,
        labels: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
    ) -> dict:
        text_embeds = self.lm.get_input_embeddings()(input_ids)
        if pixel_values is None:
            return self.lm(
                inputs_embeds=text_embeds,
                attention_mask=attention_mask
                if attention_mask is not None
                else torch.ones_like(input_ids),
                labels=labels,
            )
        visual = self.encode_images(pixel_values)
        seq = build_prepend_sequence(visual, text_embeds, labels=labels)
        return self.lm(
            inputs_embeds=seq.inputs_embeds,
            attention_mask=seq.attention_mask,
            labels=seq.labels,
        )
