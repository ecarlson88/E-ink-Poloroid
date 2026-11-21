"""Turn any photo into the 480x720, 4-bit-per-pixel frame the panel takes."""
import hashlib
import io
import json
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

WIDTH, HEIGHT = 480, 720
MAX_PIXELS = 50_000_000

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
RENDER_VERSION = 1


def render_key() -> str:
    """Fingerprint of everything that decides a frame's bytes."""
    settings = {
        "version": RENDER_VERSION,
        "size": [WIDTH, HEIGHT],
        "palette": {str(k): list(v) for k, v in sorted(PALETTE.items())},
        "high_nibble_is_left": bool(HIGH_NIBBLE_IS_LEFT),
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


def render_frame(photo: bytes) -> bytes:
    """Return exactly 172,800 bytes for the panel, or raise ValueError."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(io.BytesIO(photo))
            if img.width * img.height > MAX_PIXELS:
                raise ValueError("image has too many pixels")
            img.load()
    except ValueError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError,
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

    img = ImageOps.fit(img, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    quant = img.quantize(palette=_palette_image(), dither=Image.Dither.FLOYDSTEINBERG)
    table = bytes(_NIBBLES[i] if i < len(_NIBBLES) else 0 for i in range(256))
    nibbles = quant.tobytes().translate(table)

    first, second = nibbles[0::2], nibbles[1::2]
    if not HIGH_NIBBLE_IS_LEFT:
        first, second = second, first
    return bytes((a << 4) | b for a, b in zip(first, second))
