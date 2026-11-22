"""Turn any photo into the 480x720, 4-bit-per-pixel frame the panel takes.

The case (Erik: compact layout, 3:4 picture) masks the end of the panel at the ribbon, so a
photo fills a 480 x 640 (3:4) picture at the other end of the frame and the remaining 80 rows
stay white. Which part of the photo is used is a crop the user can move (stored per photo,
as fractions of the upright photo); the default is a centred 3:4 crop."""
import hashlib
import io
import json
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

WIDTH, HEIGHT = 480, 720
PICTURE_W, PICTURE_H = 480, 640          # the 3:4 picture the case shows
# True: the picture fills the frame's first 640 rows. That is the end away from the ribbon if
# row 0 is the top edge of the panel: an assumption until Task 1 Step 4 (corner test frame).
PICTURE_ROWS_FIRST = True
CROP_RATIO_TOLERANCE = 0.02              # how far a crop may be from 3:4 (rounding in the browser)
MAX_PIXELS = 50_000_000
UNREADABLE = "not a photo the server can read (use JPEG, PNG or WebP)"

# Nibble value -> nominal RGB. Tuned against the real panel in Task 4 Step 6.
PALETTE: dict[int, tuple[int, int, int]] = {
    0: (0, 0, 0),        # black
    1: (255, 255, 255),  # white
    2: (255, 255, 0),    # yellow
    3: (255, 0, 0),      # red
    5: (0, 0, 255),      # blue
    6: (0, 255, 0),      # green
}

# Which pixel is the high nibble. Confirmed on the bench in Task 1 Step 4.
HIGH_NIBBLE_IS_LEFT = True

_NIBBLES = sorted(PALETTE)  # palette index i -> nibble _NIBBLES[i]

# Bump when render_frame changes in a way PALETTE and HIGH_NIBBLE_IS_LEFT do
# not capture (for example a new dither), so stored frames get re-rendered.
RENDER_VERSION = 2


def render_key() -> str:
    """Fingerprint of everything that decides a frame's bytes."""
    settings = {
        "version": RENDER_VERSION,
        "size": [WIDTH, HEIGHT],
        "palette": {str(k): list(v) for k, v in sorted(PALETTE.items())},
        "high_nibble_is_left": bool(HIGH_NIBBLE_IS_LEFT),
        "picture": [PICTURE_W, PICTURE_H, bool(PICTURE_ROWS_FIRST)],
    }
    return hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()


def _palette_image() -> Image.Image:
    pal = Image.new("P", (1, 1))
    flat: list[int] = []
    for nibble in _NIBBLES:
        flat.extend(PALETTE[nibble])
    flat.extend([0] * (768 - len(flat)))
    pal.putpalette(flat)
    return pal


def _upright(photo: bytes) -> Image.Image:
    """Decode a photo, turn it upright and flatten transparency onto white.
    Raises ValueError for unusable input."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(io.BytesIO(photo))
            if img.width * img.height > MAX_PIXELS:
                raise ValueError("image has too many pixels")
            img.load()
    except ValueError:
        raise
    except UnidentifiedImageError as exc:
        raise ValueError(UNREADABLE) from exc
    except (Image.DecompressionBombError,
            Image.DecompressionBombWarning, OSError) as exc:
        raise ValueError(f"not a usable image: {exc}") from exc

    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        flat = Image.new("RGB", img.size, (255, 255, 255))
        flat.paste(img, mask=img.getchannel("A"))
        img = flat
    else:
        img = img.convert("RGB")
    return img


def photo_size(photo: bytes) -> tuple[int, int]:
    """Width and height of the photo once turned upright (what crops are relative to)."""
    return _upright(photo).size


def default_crop(w: int, h: int) -> dict:
    """The largest centred 3:4 crop of a w x h photo, as fractions."""
    target = PICTURE_W / PICTURE_H
    if w / h > target:                       # wider than 3:4: use the full height
        cw = target * h / w
        return {"x": (1 - cw) / 2, "y": 0.0, "w": cw, "h": 1.0}
    ch = w / (target * h)
    return {"x": 0.0, "y": (1 - ch) / 2, "w": 1.0, "h": ch}


def validate_crop(crop, w: int, h: int) -> dict:
    """Check a crop {x, y, w, h} (fractions of a w x h upright photo): inside the photo and
    3:4. Returns it with float values, or raises ValueError."""
    try:
        c = {k: float(crop[k]) for k in ("x", "y", "w", "h")}
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("a crop needs numbers x, y, w and h") from exc
    eps = 1e-6
    if c["w"] <= 0 or c["h"] <= 0 or c["x"] < -eps or c["y"] < -eps \
            or c["x"] + c["w"] > 1 + eps or c["y"] + c["h"] > 1 + eps:
        raise ValueError("the crop must lie inside the photo")
    ratio = (c["w"] * w) / (c["h"] * h)
    if abs(ratio / (PICTURE_W / PICTURE_H) - 1) > CROP_RATIO_TOLERANCE:
        raise ValueError("the crop must be 3:4")
    return c


def _picture(img: Image.Image, crop: dict | None) -> Image.Image:
    """Cut the crop out of an upright image and scale it to the picture size."""
    w, h = img.size
    c = validate_crop(crop, w, h) if crop is not None else default_crop(w, h)
    box = (round(c["x"] * w), round(c["y"] * h), round((c["x"] + c["w"]) * w), round((c["y"] + c["h"]) * h))
    return img.crop(box).resize((PICTURE_W, PICTURE_H), Image.Resampling.LANCZOS)


def picture_image(photo: bytes, crop: dict | None = None) -> Image.Image:
    """The picture in true color (what the web page shows for a photo)."""
    return _picture(_upright(photo), crop)


def render_frame(photo: bytes, crop: dict | None = None) -> bytes:
    """Return exactly 172,800 bytes for the panel, or raise ValueError.
    crop: fractions of the upright photo (validated); None = centred 3:4."""
    pic = _picture(_upright(photo), crop)
    img = Image.new("RGB", (WIDTH, HEIGHT), PALETTE[1])
    img.paste(pic, (0, 0) if PICTURE_ROWS_FIRST else (0, HEIGHT - PICTURE_H))
    quant = img.quantize(palette=_palette_image(), dither=Image.Dither.FLOYDSTEINBERG)
    table = bytes(_NIBBLES[i] if i < len(_NIBBLES) else 0 for i in range(256))
    nibbles = quant.tobytes().translate(table)

    first, second = nibbles[0::2], nibbles[1::2]
    if not HIGH_NIBBLE_IS_LEFT:
        first, second = second, first
    return bytes((a << 4) | b for a, b in zip(first, second))


def frame_to_image(frame: bytes) -> Image.Image:
    """Decode a packed frame back to an RGB image, as the panel will draw it
    (in PALETTE colors, which are nominal until Task 4 Step 6 tunes them)."""
    if len(frame) != WIDTH * HEIGHT // 2:
        raise ValueError("frame has the wrong length")
    high = bytes(b >> 4 for b in range(256))
    low = bytes(b & 0x0F for b in range(256))
    first, second = frame.translate(high), frame.translate(low)
    if not HIGH_NIBBLE_IS_LEFT:
        first, second = second, first
    nibbles = bytearray(WIDTH * HEIGHT)
    nibbles[0::2], nibbles[1::2] = first, second
    lut = [0] * 768
    for nibble, rgb in PALETTE.items():
        lut[nibble * 3:nibble * 3 + 3] = rgb
    img = Image.frombytes("P", (WIDTH, HEIGHT), bytes(nibbles))
    img.putpalette(lut)
    return img.convert("RGB")


def frame_picture(frame: bytes) -> Image.Image:
    """Just the picture region of a frame, decoded (the magnet preview)."""
    img = frame_to_image(frame)
    top = 0 if PICTURE_ROWS_FIRST else HEIGHT - PICTURE_H
    return img.crop((0, top, PICTURE_W, top + PICTURE_H))


def preview_original(photo: bytes, max_side: int = 1600) -> Image.Image:
    """The whole photo, upright, scaled down to at most max_side: what the crop editor shows."""
    img = _upright(photo)
    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return img
