"""SigLIP encoder wrapper + PseudoDeepStack feature extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import torch
import torch.nn as nn

from cobra_kc001 import DEFAULT_PSEUDO_LAYERS, SIGLIP_HIDDEN_SIZE
from cobra_kc001.projector import assert_finite


@dataclass(frozen=True)
class EncoderSpec:
    model_id: str = "google/siglip-so400m-patch14-384"
    image_size: int = 384
    patch_size: int = 14
    hidden_size: int = SIGLIP_HIDDEN_SIZE
    num_layers: int = 27
    pseudo_layers: tuple[int, ...] = DEFAULT_PSEUDO_LAYERS

    @property
    def image_tokens(self) -> int:
        side = self.image_size // self.patch_size
        return side * side


class PseudoDeepStackEncoder(nn.Module):
    """Frozen SigLIP vision tower with multi-depth feature concat.

    When `vision` is None, operates in stub mode for unit tests
    (random but deterministic features from a tiny Conv patch embed).
    """

    def __init__(
        self,
        vision: nn.Module | None = None,
        *,
        spec: EncoderSpec | None = None,
        stub: bool = False,
        stub_dim: int = SIGLIP_HIDDEN_SIZE,
    ) -> None:
        super().__init__()
        self.spec = spec or EncoderSpec()
        self.stub = stub or vision is None
        self.vision = vision
        if self.stub:
            # Cheap stand-in: produces [B, 729, 1152] "layer" features.
            self.stub_proj = nn.Conv2d(3, stub_dim, kernel_size=14, stride=14)
            self._stub_layers = nn.ModuleList(
                [nn.Linear(stub_dim, stub_dim) for _ in self.spec.pseudo_layers]
            )
        else:
            self.stub_proj = None
            self._stub_layers = None
        self.freeze_encoder()

    def freeze_encoder(self) -> None:
        if self.vision is not None:
            self.vision.eval()
            for p in self.vision.parameters():
                p.requires_grad = False
        if self.stub_proj is not None:
            for p in self.stub_proj.parameters():
                p.requires_grad = False
            assert self._stub_layers is not None
            for layer in self._stub_layers:
                for p in layer.parameters():
                    p.requires_grad = False

    @torch.no_grad()
    def forward_features(self, pixel_values: torch.Tensor) -> torch.Tensor:
        """Return PseudoDeepStack concat features [B, T, 3456]."""
        if self.stub:
            return self._stub_features(pixel_values)
        assert self.vision is not None
        out = self.vision(pixel_values=pixel_values, output_hidden_states=True)
        hs = out.hidden_states
        picked = []
        for li in self.spec.pseudo_layers:
            if li < 0 or li >= len(hs):
                raise IndexError(f"pseudo layer {li} out of range (len={len(hs)})")
            feat = hs[li]
            # Drop CLS if present (SigLIP vision usually patch tokens only at 729).
            if feat.shape[1] == self.spec.image_tokens + 1:
                feat = feat[:, 1:, :]
            picked.append(feat)
        features = torch.cat(picked, dim=-1)
        assert_finite(features, "pseudo_deepstack_features")
        return features

    def _stub_features(self, pixel_values: torch.Tensor) -> torch.Tensor:
        assert self.stub_proj is not None and self._stub_layers is not None
        x = self.stub_proj(pixel_values)  # [B, C, H', W']
        b, c, h, w = x.shape
        tokens = x.flatten(2).transpose(1, 2)  # [B, T, C]
        # Pad / truncate to expected token count for stable tests.
        need = self.spec.image_tokens
        if tokens.shape[1] < need:
            pad = tokens.new_zeros(b, need - tokens.shape[1], c)
            tokens = torch.cat([tokens, pad], dim=1)
        elif tokens.shape[1] > need:
            tokens = tokens[:, :need, :]
        parts = [layer(tokens) for layer in self._stub_layers]
        features = torch.cat(parts, dim=-1)
        assert_finite(features, "stub_pseudo_features")
        return features


def load_siglip(model_id: str | None = None, device: str = "cpu"):
    """Optional heavy loader — requires network / local cache."""
    from transformers import SiglipImageProcessor, SiglipVisionModel

    mid = model_id or EncoderSpec().model_id
    processor = SiglipImageProcessor.from_pretrained(mid)
    vision = SiglipVisionModel.from_pretrained(mid, torch_dtype=torch.float32)
    vision.to(device).eval()
    return processor, vision
