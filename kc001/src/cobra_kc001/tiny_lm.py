"""Tiny GPT-OSS-shaped MoE LM for architecture proofs without 20B weights."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class TinyGptOssConfig:
    vocab_size: int = 512
    hidden_size: int = 128
    intermediate_size: int = 256
    num_hidden_layers: int = 4
    num_attention_heads: int = 4
    num_local_experts: int = 8
    num_experts_per_tok: int = 2
    max_position_embeddings: int = 2048
    rms_norm_eps: float = 1e-5


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-5) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        var = x.pow(2).mean(dim=-1, keepdim=True)
        x = x * torch.rsqrt(var + self.eps)
        return self.weight * x


class TinyAttention(nn.Module):
    def __init__(self, cfg: TinyGptOssConfig) -> None:
        super().__init__()
        self.heads = cfg.num_attention_heads
        self.head_dim = cfg.hidden_size // cfg.num_attention_heads
        self.qkv = nn.Linear(cfg.hidden_size, 3 * cfg.hidden_size)
        self.o = nn.Linear(cfg.hidden_size, cfg.hidden_size)

    def forward(self, x: torch.Tensor, attn_mask: torch.Tensor | None = None) -> torch.Tensor:
        b, t, h = x.shape
        qkv = self.qkv(x).view(b, t, 3, self.heads, self.head_dim)
        q, k, v = qkv.unbind(dim=2)
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        scores = (q @ k.transpose(-2, -1)) / (self.head_dim**0.5)
        causal = torch.triu(torch.ones(t, t, device=x.device, dtype=torch.bool), diagonal=1)
        scores = scores.masked_fill(causal, torch.finfo(scores.dtype).min)
        if attn_mask is not None:
            # attn_mask: [B, T] ones for keep
            am = attn_mask[:, None, None, :].to(dtype=torch.bool)
            scores = scores.masked_fill(~am, torch.finfo(scores.dtype).min)
        w = torch.softmax(scores, dim=-1)
        out = (w @ v).transpose(1, 2).contiguous().view(b, t, h)
        return self.o(out)


class TinyMoE(nn.Module):
    def __init__(self, cfg: TinyGptOssConfig) -> None:
        super().__init__()
        self.num_experts = cfg.num_local_experts
        self.k = cfg.num_experts_per_tok
        self.router = nn.Linear(cfg.hidden_size, cfg.num_local_experts, bias=False)
        self.experts = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Linear(cfg.hidden_size, cfg.intermediate_size),
                    nn.SiLU(),
                    nn.Linear(cfg.intermediate_size, cfg.hidden_size),
                )
                for _ in range(cfg.num_local_experts)
            ]
        )
        self.last_router_logits: torch.Tensor | None = None
        self.last_selected: torch.Tensor | None = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.router(x)  # [B, T, E]
        self.last_router_logits = logits
        probs = torch.softmax(logits, dim=-1)
        topv, topi = torch.topk(probs, k=self.k, dim=-1)
        self.last_selected = topi
        topv = topv / topv.sum(dim=-1, keepdim=True).clamp_min(1e-9)
        out = torch.zeros_like(x)
        for i in range(self.k):
            idx = topi[..., i]
            w = topv[..., i].unsqueeze(-1)
            # Gather expert outputs (simple loop; tiny model only)
            expert_out = torch.zeros_like(x)
            for e, expert in enumerate(self.experts):
                mask = idx == e
                if mask.any():
                    expert_out = torch.where(mask.unsqueeze(-1), expert(x), expert_out)
            out = out + w * expert_out
        return out


class TinyBlock(nn.Module):
    def __init__(self, cfg: TinyGptOssConfig) -> None:
        super().__init__()
        self.norm1 = RMSNorm(cfg.hidden_size, cfg.rms_norm_eps)
        self.attn = TinyAttention(cfg)
        self.norm2 = RMSNorm(cfg.hidden_size, cfg.rms_norm_eps)
        self.mlp = TinyMoE(cfg)

    def forward(self, x: torch.Tensor, attn_mask: torch.Tensor | None = None) -> torch.Tensor:
        x = x + self.attn(self.norm1(x), attn_mask)
        x = x + self.mlp(self.norm2(x))
        return x


class TinyGptOssForCausalLM(nn.Module):
    """Minimal causal LM with MoE MLP — GPT-OSS-shaped for KC-001 proofs."""

    def __init__(self, cfg: TinyGptOssConfig | None = None) -> None:
        super().__init__()
        self.cfg = cfg or TinyGptOssConfig()
        self.embed_tokens = nn.Embedding(self.cfg.vocab_size, self.cfg.hidden_size)
        self.layers = nn.ModuleList([TinyBlock(self.cfg) for _ in range(self.cfg.num_hidden_layers)])
        self.norm = RMSNorm(self.cfg.hidden_size, self.cfg.rms_norm_eps)
        self.lm_head = nn.Linear(self.cfg.hidden_size, self.cfg.vocab_size, bias=False)

    def get_input_embeddings(self) -> nn.Embedding:
        return self.embed_tokens

    def forward(
        self,
        input_ids: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor | list]:
        if inputs_embeds is None:
            if input_ids is None:
                raise ValueError("input_ids or inputs_embeds required")
            inputs_embeds = self.embed_tokens(input_ids)
        x = inputs_embeds
        routing: list[dict] = []
        for layer in self.layers:
            x = layer(x, attention_mask)
            moe = layer.mlp
            routing.append(
                {
                    "router_logits": moe.last_router_logits.detach() if moe.last_router_logits is not None else None,
                    "selected": moe.last_selected.detach() if moe.last_selected is not None else None,
                }
            )
        x = self.norm(x)
        logits = self.lm_head(x)
        loss = None
        if labels is not None:
            # Shift for causal LM
            shift_logits = logits[:, :-1, :].contiguous()
            shift_labels = labels[:, 1:].contiguous()
            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100,
            )
        return {"loss": loss, "logits": logits, "routing": routing}

    @torch.no_grad()
    def generate(self, inputs_embeds: torch.Tensor, max_new_tokens: int = 8) -> torch.Tensor:
        x = inputs_embeds
        generated: list[int] = []
        for _ in range(max_new_tokens):
            out = self.forward(inputs_embeds=x)
            next_id = int(out["logits"][0, -1].argmax())
            generated.append(next_id)
            tok = self.embed_tokens(torch.tensor([[next_id]], device=x.device))
            x = torch.cat([x, tok], dim=1)
        return torch.tensor(generated, device=inputs_embeds.device)
