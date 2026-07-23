import io

import pytest
from PIL import Image

from cobra_kc001.safety import ImageLimits, UnsafeImageError, load_image_safe, validate_image_batch_count


def _png_bytes(size=(32, 32), color=(10, 20, 30)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_load_ok():
    img = load_image_safe(_png_bytes())
    assert img.mode == "RGB"
    assert img.info == {}


def test_reject_oversized_bytes():
    data = _png_bytes()
    with pytest.raises(UnsafeImageError):
        load_image_safe(data, ImageLimits(max_bytes=10))


def test_reject_too_many_pixels():
    data = _png_bytes(size=(64, 64))
    with pytest.raises(UnsafeImageError):
        load_image_safe(data, ImageLimits(max_pixels=100))


def test_reject_garbage():
    with pytest.raises(UnsafeImageError):
        load_image_safe(b"not-an-image")


def test_max_images():
    with pytest.raises(UnsafeImageError):
        validate_image_batch_count(9, ImageLimits(max_images=4))
