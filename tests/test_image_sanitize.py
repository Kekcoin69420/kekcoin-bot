from io import BytesIO

import pytest
from PIL import Image

from image_sanitize import strip_image_metadata


def _jpeg_with_exif() -> bytes:
    img = Image.new("RGB", (32, 32), color=(40, 80, 120))
    exif = Image.Exif()
    exif[0x9286] = "Temple test metadata"
    exif[0x010E] = "GPS test"
    buf = BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def test_strip_removes_jpeg_exif():
    raw = _jpeg_with_exif()
    result = strip_image_metadata(raw)
    assert result is not None
    clean, ext = result
    assert ext == "jpg"
    with Image.open(BytesIO(clean)) as out:
        assert not out.getexif()


def test_strip_png_no_info():
    buf = BytesIO()
    Image.new("RGBA", (16, 16), (255, 0, 0, 128)).save(buf, format="PNG")
    result = strip_image_metadata(buf.getvalue())
    assert result is not None
    clean, ext = result
    assert ext == "png"
    with Image.open(BytesIO(clean)) as out:
        assert len(out.info) == 0


def test_rejects_oversized():
    assert strip_image_metadata(b"x" * (5 * 1024 * 1024 + 1)) is None