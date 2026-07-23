"""MoE routing instrumentation for text vs image conditions."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from cobra_kc001.multimodal import CobraTinyVisionLM


@dataclass
class RoutingSummary:
    condition: str
    mean_entropy: float
    expert_load: list[float]
    image_token_expert_hist: list[float] | None
    text_token_expert_hist: list[float] | None


def _entropy(probs: torch.Tensor) -> torch.Tensor:
    # probs [..., E]
    return -(probs * (probs + 1e-9).log()).sum(dim=-1)


def summarize_routing(
    model: CobraTinyVisionLM,
    *,
    condition: str,
    pixel_values: torch.Tensor | None,
    input_ids: torch.Tensor,
    image_token_count: int,
) -> RoutingSummary:
    model.eval()
    with torch.no_grad():
        out = model(pixel_values=pixel_values, input_ids=input_ids)
    entropies = []
    loads = None
    img_hist = None
    txt_hist = None
    n_experts = model.lm.cfg.num_local_experts
    for layer in out["routing"]:
        logits = layer["router_logits"]
        selected = layer["selected"]
        if logits is None or selected is None:
            continue
        probs = torch.softmax(logits, dim=-1)
        entropies.append(float(_entropy(probs).mean()))
        # load: fraction of tokens selecting each expert (top-1)
        top1 = selected[..., 0]
        hist = torch.bincount(top1.reshape(-1), minlength=n_experts).float()
        hist = hist / hist.sum().clamp_min(1)
        loads = hist if loads is None else loads + hist
        if image_token_count > 0 and pixel_values is not None:
            img = top1[:, :image_token_count]
            txt = top1[:, image_token_count:]
            ih = torch.bincount(img.reshape(-1), minlength=n_experts).float()
            th = torch.bincount(txt.reshape(-1), minlength=n_experts).float()
            ih = ih / ih.sum().clamp_min(1)
            th = th / th.sum().clamp_min(1)
            img_hist = ih if img_hist is None else img_hist + ih
            txt_hist = th if txt_hist is None else txt_hist + th
    n = max(1, len(entropies))
    if loads is not None:
        loads = loads / n
    if img_hist is not None:
        img_hist = img_hist / n
        txt_hist = txt_hist / n
    return RoutingSummary(
        condition=condition,
        mean_entropy=sum(entropies) / max(1, len(entropies)),
        expert_load=(loads.tolist() if loads is not None else []),
        image_token_expert_hist=(img_hist.tolist() if img_hist is not None else None),
        text_token_expert_hist=(txt_hist.tolist() if txt_hist is not None else None),
    )


def compare_conditions(model: CobraTinyVisionLM, input_ids: torch.Tensor, images: dict[str, torch.Tensor | None]):
    """images: name -> pixel_values or None."""
    results = []
    # Infer image token count from encoder spec when present.
    t_img = model.encoder.spec.image_tokens
    for name, pix in images.items():
        results.append(
            summarize_routing(
                model,
                condition=name,
                pixel_values=pix,
                input_ids=input_ids,
                image_token_count=0 if pix is None else t_img,
            )
        )
    return results
