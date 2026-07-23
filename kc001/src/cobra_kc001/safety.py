"""Image ingest safety limits for KC-001 (no metadata execution)."""

from __future__ import annotations

import io
import os
from dataclasses import dataclass

from PIL import Image, ImageFile, UnidentifiedImageError

# Refuse truncated bombs by default.
ImageFile.LOAD_TRUNCATED_IMAGES = False


@dataclass(frozen=True)
class ImageLimits:
    max_bytes: int = int(os.environ.get("COBRA_MAX_IMAGE_BYTES", 8_000_000))
    max_pixels: int = int(os.environ.get("COBRA_MAX_IMAGE_PIXELS", 20_000_000))
    max_images: int = int(os.environ.get("COBRA_MAX_IMAGES", 4))
    max_dimension: int = 8192
    allowed_formats: tuple[str, ...] = ("JPEG", "PNG", "WEBP", "BMP")


class UnsafeImageError(ValueError):
    pass


def load_image_safe(data: bytes, limits: ImageLimits | None = None) -> Image.Image:
    limits = limits or ImageLimits()
    if len(data) > limits.max_bytes:
        raise UnsafeImageError(f"image exceeds max_bytes={limits.max_bytes}")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise UnsafeImageError(f"malformed image: {exc}") from exc
    fmt = (img.format or "").upper()
    if fmt not in limits.allowed_formats:
        raise UnsafeImageError(f"unsupported format: {fmt or 'unknown'}")
    w, h = img.size
    if w > limits.max_dimension or h > limits.max_dimension:
        raise UnsafeImageError("dimension exceeds max_dimension")
    if w * h > limits.max_pixels:
        raise UnsafeImageError("decoded pixels exceed max_pixels")
    # Drop EXIF / info — never execute metadata.
    rgb = img.convert("RGB")
    rgb.info = {}
    return rgb


def validate_image_batch_count(n: int, limits: ImageLimits | None = None) -> None:
    limits = limits or ImageLimits()
    if n > limits.max_images:
        raise UnsafeImageError(f"too many images: {n} > {limits.max_images}")
