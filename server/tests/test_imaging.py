import io

import pytest
from PIL import Image

import imaging
from imaging import PALETTE, default_crop, frame_picture, frame_to_image, photo_size, render_frame, validate_crop

FRAME_BYTES = 172_800
RED = PALETTE[3]
ROW_BYTES = 240              # 480 pixels per row, 2 per byte
PICTURE_BYTES = 640 * ROW_BYTES   # the 3:4 picture: the frame's first 640 rows (Erik: 3:4)


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
    """The picture fills the first 640 rows; the 80 rows at the ribbon end stay white."""
    margin = b"\x11" * (FRAME_BYTES - PICTURE_BYTES)
    black = render_frame(_png(Image.new("RGB", (480, 640), PALETTE[0])))
    white = render_frame(_png(Image.new("RGB", (480, 640), PALETTE[1])))
    red = render_frame(_png(Image.new("RGB", (480, 640), RED)))
    assert black == b"\x00" * PICTURE_BYTES + margin
    assert white == b"\x11" * FRAME_BYTES
    assert red == b"\x33" * PICTURE_BYTES + margin


def test_picture_at_the_other_end_when_rows_last(monkeypatch):
    monkeypatch.setattr(imaging, "PICTURE_ROWS_FIRST", False)
    red = render_frame(_png(Image.new("RGB", (480, 640), RED)))
    assert red == b"\x11" * (FRAME_BYTES - PICTURE_BYTES) + b"\x33" * PICTURE_BYTES


def test_wide_photo_fills_the_picture():
    frame = render_frame(_png(Image.new("RGB", (1000, 300), RED)))
    assert 1 not in _nibbles(frame[:PICTURE_BYTES])


def test_exif_rotation_applied():
    img = Image.new("RGB", (600, 400), PALETTE[3])
    img.paste(Image.new("RGB", (300, 400), PALETTE[5]), (300, 0))  # right half blue
    exif = Image.Exif()
    exif[0x0112] = 6  # display rotated 90 degrees clockwise
    frame = render_frame(_png(img, exif=exif))
    nibbles = _nibbles(frame[:PICTURE_BYTES])
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



def test_frame_to_image_round_trips_exact_pixels():
    """Palette-colored 1-px stripes, different in the top and bottom halves,
    must come back pixel for pixel (catches nibble-order and row mistakes)."""
    img = Image.new("RGB", (480, 640))
    top, bottom = (PALETTE[0], PALETTE[2]), (PALETTE[5], PALETTE[3])
    for y in range(640):
        pair = top if y < 320 else bottom
        for x in range(480):
            img.putpixel((x, y), pair[x % 2])
    frame = render_frame(_png(img))
    out = frame_to_image(frame)
    assert out.mode == "RGB" and out.size == (480, 720)
    assert out.crop((0, 0, 480, 640)).tobytes() == img.tobytes()
    assert frame_picture(frame).tobytes() == img.tobytes()     # just the picture region


# --- Crop (Erik: the user can move the 3:4 crop around) ---------------------------------------

def _halves(w=1200, h=600):
    """Left half red, right half blue."""
    img = Image.new("RGB", (w, h), RED)
    img.paste(Image.new("RGB", (w // 2, h), PALETTE[5]), (w // 2, 0))
    return _png(img)


def test_default_crop_is_centred_3_4():
    c = default_crop(1200, 600)
    assert c["h"] == 1 and abs(c["w"] * 1200 / (c["h"] * 600) - 0.75) < 1e-9
    assert abs(c["x"] + c["w"] / 2 - 0.5) < 1e-9 and c["y"] == 0
    tall = default_crop(600, 1200)
    assert tall["w"] == 1 and abs(tall["y"] + tall["h"] / 2 - 0.5) < 1e-9


def test_crop_selects_that_part_of_the_photo():
    w = 600 * 0.75 / 1200            # a full-height 3:4 crop of a 1200 x 600 photo
    left = render_frame(_halves(), {"x": 0.0, "y": 0.0, "w": w, "h": 1.0})
    right = render_frame(_halves(), {"x": 1 - w, "y": 0.0, "w": w, "h": 1.0})
    assert set(_nibbles(left[:PICTURE_BYTES])) == {3}
    assert set(_nibbles(right[:PICTURE_BYTES])) == {5}


def test_crop_must_be_inside_the_photo_and_3_4():
    w = 600 * 0.75 / 1200
    assert validate_crop({"x": 0.1, "y": 0, "w": w, "h": 1}, 1200, 600)
    for bad in ({"x": 0.9, "y": 0, "w": w, "h": 1},           # runs off the right edge
                {"x": 0, "y": 0, "w": 0.5, "h": 1},            # not 3:4
                {"x": 0, "y": 0, "w": 0, "h": 0},              # empty
                {"x": 0, "y": 0, "w": w},                      # missing a field
                {"x": "a", "y": 0, "w": w, "h": 1}):           # not a number
        with pytest.raises(ValueError):
            validate_crop(bad, 1200, 600)


def test_photo_size_is_upright():
    img = Image.new("RGB", (600, 400))
    exif = Image.Exif()
    exif[0x0112] = 6
    assert photo_size(_png(img, exif=exif)) == (400, 600)
