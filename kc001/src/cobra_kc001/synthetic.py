"""Procedural images for overfit / dependence tests (no copyrighted assets)."""

from __future__ import annotations

import hashlib

import numpy as np
import torch
from PIL import Image, ImageDraw


COLORS = {
    "red": (220, 40, 40),
    "green": (40, 180, 60),
    "blue": (40, 80, 220),
    "yellow": (230, 210, 40),
}


def make_solid_image(color: str, size: int = 384) -> Image.Image:
    rgb = COLORS[color]
    img = Image.new("RGB", (size, size), rgb)
    draw = ImageDraw.Draw(img)
    draw.rectangle([size // 4, size // 4, 3 * size // 4, 3 * size // 4], outline=(0, 0, 0), width=8)
    return img


def make_blank(size: int = 384) -> Image.Image:
    return Image.new("RGB", (size, size), (0, 0, 0))


def make_noise(size: int = 384, seed: int = 0) -> Image.Image:
    rng = np.random.default_rng(seed)
    arr = rng.integers(0, 256, size=(size, size, 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def pil_to_tensor(img: Image.Image, size: int = 112) -> torch.Tensor:
    img = img.convert("RGB").resize((size, size))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = (arr - 0.5) / 0.5
    return torch.from_numpy(arr).permute(2, 0, 1).contiguous()


def build_color_dataset(n: int = 16) -> list[tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
    """Return list of (pixel_values[1,3,H,W], input_ids[1,T], labels[1,T])."""
    colors = list(COLORS.keys())
    out: list[tuple[torch.Tensor, torch.Tensor, torch.Tensor]] = []
    for i in range(n):
        color = colors[i % len(colors)]
        ans = 20 + (i % len(colors))
        pix = pil_to_tensor(make_solid_image(color, size=112)).unsqueeze(0)
        input_ids = torch.tensor([[10, 11, 12, ans]], dtype=torch.long)
        labels = torch.tensor([[-100, -100, -100, ans]], dtype=torch.long)
        out.append((pix, input_ids, labels))
    return out


def example_hash(color: str, idx: int) -> str:
    return hashlib.sha256(f"{color}:{idx}".encode()).hexdigest()[:16]
