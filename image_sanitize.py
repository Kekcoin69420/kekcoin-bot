"""Strip EXIF and all image metadata by decoding and re-encoding pixels only."""
from __future__ import annotations

import logging
from io import BytesIO

log = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_INPUT = {"JPEG", "PNG", "WEBP", "GIF", "MPO"}


def strip_image_metadata(data: bytes) -> tuple[bytes, str] | None:
    """
    Re-encode image bytes without metadata (EXIF, ICC, XMP, comments).
    Returns (clean_bytes, ext) or None if unreadable / over size limit.
    Animated images use the first frame only.
    """
    if len(data) > MAX_IMAGE_BYTES:
        log.warning("strip_image_metadata: file too large (%s bytes)", len(data))
        return None

    try:
        from PIL import Image
    except ImportError:
        log.error("Pillow not installed — cannot strip image metadata")
        return None

    try:
        with Image.open(BytesIO(data)) as src:
            if src.format not in ALLOWED_INPUT:
                log.warning("strip_image_metadata: unsupported format %s", src.format)
                return None

            if getattr(src, "is_animated", False):
                src.seek(0)

            src.load()

            has_alpha = (
                src.mode in ("RGBA", "LA")
                or (src.mode == "P" and "transparency" in src.info)
            )

            if src.mode == "P":
                work = src.convert("RGBA")
            elif src.mode == "LA":
                work = src.convert("RGBA")
            elif src.mode == "RGBA":
                work = src
            else:
                work = src.convert("RGB")
                has_alpha = False

            out = BytesIO()
            if has_alpha:
                work.save(out, format="PNG", optimize=True)
                return out.getvalue(), "png"

            work.save(out, format="JPEG", quality=88, subsampling=0)
            return out.getvalue(), "jpg"

    except Exception as e:
        log.warning("strip_image_metadata failed: %s", e)
        return None