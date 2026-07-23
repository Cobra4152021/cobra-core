"""GPT-OSS integration: inject projected image embeddings into the LM stream."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn

from cobra_kc001 import IMAGE_PAD_TOKEN


@dataclass
class MultimodalSequence:
    inputs_embeds: torch.Tensor
    attention_mask: torch.Tensor
    position_ids: torch.Tensor
    labels: torch.Tensor | None
    image_token_count: int
    text_token_count: int


def build_prepend_sequence(
    visual_tokens: torch.Tensor,
    text_embeds: torch.Tensor,
    *,
    labels: torch.Tensor | None = None,
    pad_label: int = -100,
) -> MultimodalSequence:
    """Prepend visual tokens (upstream GPT-OSS-Vision preview style).

    visual_tokens: [B, T_img, H]
    text_embeds:   [B, T_txt, H]
    labels:        [B, T_txt] optional — image positions masked with pad_label
    """
    if visual_tokens.ndim != 3 or text_embeds.ndim != 3:
        raise ValueError("visual_tokens and text_embeds must be rank-3")
    if visual_tokens.shape[0] != text_embeds.shape[0]:
        raise ValueError("batch mismatch")
    if visual_tokens.shape[-1] != text_embeds.shape[-1]:
        raise ValueError("hidden size mismatch between image and text embeds")
    if visual_tokens.device != text_embeds.device:
        raise RuntimeError("image/text embeds on different devices")

    b, t_img, _ = visual_tokens.shape
    t_txt = text_embeds.shape[1]
    inputs_embeds = torch.cat([visual_tokens, text_embeds], dim=1)
    attention_mask = torch.ones(b, t_img + t_txt, device=inputs_embeds.device, dtype=torch.long)
    position_ids = torch.arange(t_img + t_txt, device=inputs_embeds.device).unsqueeze(0).expand(b, -1)
    out_labels = None
    if labels is not None:
        if labels.shape != (b, t_txt):
            raise ValueError(f"labels shape {tuple(labels.shape)} != {(b, t_txt)}")
        img_labels = torch.full((b, t_img), pad_label, device=labels.device, dtype=labels.dtype)
        out_labels = torch.cat([img_labels, labels], dim=1)
    return MultimodalSequence(
        inputs_embeds=inputs_embeds,
        attention_mask=attention_mask,
        position_ids=position_ids,
        labels=out_labels,
        image_token_count=t_img,
        text_token_count=t_txt,
    )


def replace_image_pad_embeddings(
    input_ids: torch.Tensor,
    inputs_embeds: torch.Tensor,
    visual_tokens: torch.Tensor,
    image_pad_id: int,
    *,
    max_context: int | None = None,
) -> torch.Tensor:
    """Scatter visual tokens into IMAGE_PAD placeholder positions.

    Asserts:
    - per-sample pad count == visual_tokens length
    - text-only rows do not receive image tensors
    """
    if input_ids.shape[:2] != inputs_embeds.shape[:2]:
        raise ValueError("input_ids / inputs_embeds length mismatch")
    if visual_tokens.device != inputs_embeds.device:
        raise RuntimeError("visual_tokens on wrong device")

    b = input_ids.shape[0]
    out = inputs_embeds.clone()
    t_img = visual_tokens.shape[1]
    for i in range(b):
        pad_pos = (input_ids[i] == image_pad_id).nonzero(as_tuple=False).flatten()
        if pad_pos.numel() == 0:
            # Text-only: must not inject
            continue
        if pad_pos.numel() != t_img:
            raise AssertionError(
                f"batch {i}: image pad count {pad_pos.numel()} != visual tokens {t_img}"
            )
        out[i, pad_pos] = visual_tokens[i]
    if max_context is not None and out.shape[1] > max_context:
        raise AssertionError(f"sequence length {out.shape[1]} exceeds context {max_context}")
    return out


def assert_labels_mask_image_positions(labels: torch.Tensor, image_mask: torch.Tensor) -> None:
    """Fail if any image position has a non-ignored label."""
    bad = image_mask & (labels != -100)
    if bad.any():
        raise AssertionError("labels train on image placeholder positions")


class EmbeddingInjector(nn.Module):
    """Thin helper around an LM embedding table + projector outputs."""

    def __init__(self, embed_tokens: nn.Embedding, image_pad_id: int | None = None) -> None:
        super().__init__()
        self.embed_tokens = embed_tokens
        self.image_pad_id = image_pad_id

    def text_embeds(self, input_ids: torch.Tensor) -> torch.Tensor:
        return self.embed_tokens(input_ids)

    def build(
        self,
        input_ids: torch.Tensor,
        visual_tokens: torch.Tensor | None,
        *,
        mode: str = "prepend",
        labels: torch.Tensor | None = None,
        max_context: int | None = None,
    ) -> MultimodalSequence:
        text = self.text_embeds(input_ids)
        if visual_tokens is None:
            b, t, _ = text.shape
            mask = torch.ones(b, t, device=text.device, dtype=torch.long)
            pos = torch.arange(t, device=text.device).unsqueeze(0).expand(b, -1)
            return MultimodalSequence(text, mask, pos, labels, 0, t)

        if mode == "prepend":
            seq = build_prepend_sequence(visual_tokens, text, labels=labels)
        elif mode == "replace_pad":
            if self.image_pad_id is None:
                raise ValueError("image_pad_id required for replace_pad mode")
            embeds = replace_image_pad_embeddings(
                input_ids, text, visual_tokens, self.image_pad_id, max_context=max_context
            )
            b, t, _ = embeds.shape
            mask = torch.ones(b, t, device=embeds.device, dtype=torch.long)
            pos = torch.arange(t, device=embeds.device).unsqueeze(0).expand(b, -1)
            # Labels already aligned to input_ids length for replace mode.
            if labels is not None:
                image_mask = input_ids == self.image_pad_id
                assert_labels_mask_image_positions(labels, image_mask)
            seq = MultimodalSequence(embeds, mask, pos, labels, visual_tokens.shape[1], input_ids.shape[1])
        else:
            raise ValueError(f"unknown mode: {mode}")
        if max_context is not None and seq.inputs_embeds.shape[1] > max_context:
            raise AssertionError("sequence length exceeds context")
        return seq


def register_image_pad_token(tokenizer, token: str = IMAGE_PAD_TOKEN) -> int:
    """Add a special image pad token if missing; return its id."""
    existing = tokenizer.convert_tokens_to_ids(token)
    unk = getattr(tokenizer, "unk_token_id", None)
    if existing is not None and existing != unk and existing >= 0:
        # Heuristic: if tokenizer already knows it, keep.
        if tokenizer.convert_ids_to_tokens(existing) == token:
            return int(existing)
    tokenizer.add_special_tokens({"additional_special_tokens": [token]})
    return int(tokenizer.convert_tokens_to_ids(token))
