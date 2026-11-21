import io

import pytest
from PIL import Image

from imaging import PALETTE, render_frame

FRAME_BYTES = 172_800
RED = PALETTE[3]


def _png(img: Image.Image, **save_kwargs) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", **save_kwargs)
    return buf.getvalue()


def _jpeg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _nibbles(frame: bytes) -> list[int]:
    out = []
    for b in frame:
        out.append(b >> 4)
        out.append(b & 0x0F)
    return out


def test_frame_length():
    photo = _jpeg(Image.new("RGB", (800, 600), (120, 90, 60)))
    assert len(render_frame(photo)) == FRAME_BYTES


def test_solid_colors_are_exact():
    black = render_frame(_png(Image.new("RGB", (480, 720), PALETTE[0])))
    white = render_frame(_png(Image.new("RGB", (480, 720), PALETTE[1])))
    red = render_frame(_png(Image.new("RGB", (480, 720), RED)))
    assert black == b"\x00" * FRAME_BYTES
    assert white == b"\x11" * FRAME_BYTES
    assert red == b"\x33" * FRAME_BYTES


def test_wide_photo_fills_frame():
    frame = render_frame(_png(Image.new("RGB", (1000, 300), RED)))
    assert 1 not in _nibbles(frame)


def test_exif_rotation_applied():
    img = Image.new("RGB", (600, 400), PALETTE[3])
    img.paste(Image.new("RGB", (300, 400), PALETTE[5]), (300, 0))  # right half blue
    exif = Image.Exif()
    exif[0x0112] = 6  # display rotated 90 degrees clockwise
    frame = render_frame(_png(img, exif=exif))
    nibbles = _nibbles(frame)
    half = len(nibbles) // 2
    top, bottom = nibbles[:half], nibbles[half:]
    assert top.count(3) > 0.9 * len(top)
    assert bottom.count(5) > 0.9 * len(bottom)


def test_rejects_non_image():
    with pytest.raises(ValueError):
        render_frame(b"hello")


def test_rejects_decompression_bomb():
    with pytest.raises(ValueError):
        render_frame(_png(Image.new("1", (10_000, 10_000))))
