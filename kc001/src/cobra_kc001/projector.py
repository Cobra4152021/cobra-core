"""Multimodal projector: PseudoDeepStack features → GPT-OSS hidden size."""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn as nn

from cobra_kc001 import GPT_OSS_HIDDEN_SIZE, PSEUDO_DEEPSTACK_DIM


@dataclass(frozen=True)
class ProjectorConfig:
    in_dim: int = PSEUDO_DEEPSTACK_DIM
    hidden_dim: int = GPT_OSS_HIDDEN_SIZE
    out_dim: int = GPT_OSS_HIDDEN_SIZE
    activation: str = "gelu"


class VisionProjector(nn.Module):
    """Two-layer MLP matching the public GPT-OSS-20B-Vision preview design.

    Input:  [B, T_img, 3456]  (concat of three SigLIP depths @ 1152)
    Output: [B, T_img, 2880]  (GPT-OSS hidden size)
    """

    def __init__(self, cfg: ProjectorConfig | None = None) -> None:
        super().__init__()
        self.cfg = cfg or ProjectorConfig()
        act: nn.Module
        if self.cfg.activation == "gelu":
            act = nn.GELU()
        elif self.cfg.activation == "silu":
            act = nn.SiLU()
        else:
            raise ValueError(f"unsupported activation: {self.cfg.activation}")
        self.net = nn.Sequential(
            nn.Linear(self.cfg.in_dim, self.cfg.hidden_dim),
            act,
            nn.Linear(self.cfg.hidden_dim, self.cfg.out_dim),
        )
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for mod in self.net:
            if isinstance(mod, nn.Linear):
                nn.init.xavier_uniform_(mod.weight)
                nn.init.zeros_(mod.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 3:
            raise ValueError(f"expected [B,T,C], got {tuple(x.shape)}")
        if x.shape[-1] != self.cfg.in_dim:
            raise ValueError(f"expected last dim {self.cfg.in_dim}, got {x.shape[-1]}")
        return self.net(x)

    def param_count(self) -> int:
        return sum(p.numel() for p in self.parameters())


def expected_projector_params(cfg: ProjectorConfig | None = None) -> int:
    cfg = cfg or ProjectorConfig()
    # Linear(in,h) + bias + Linear(h,out) + bias
    return (cfg.in_dim * cfg.hidden_dim + cfg.hidden_dim) + (
        cfg.hidden_dim * cfg.out_dim + cfg.out_dim
    )


def assert_finite(t: torch.Tensor, name: str = "tensor") -> None:
    if not torch.isfinite(t).all():
        raise RuntimeError(f"{name} contains non-finite values")
    peak = float(t.detach().abs().max()) if t.numel() else 0.0
    if peak > 1e6:
        # Soft check: extremely large activations often indicate scale bugs.
        raise RuntimeError(f"{name} has extreme magnitude ({peak:.3e})")
