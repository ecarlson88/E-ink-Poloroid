"""Bench test frames for the panel, written to firmware/bench/test_frames.h.

corner frame (Task 1 Step 4): answers three questions on the bench.
  - Orientation: red = the first bytes sent (row 0, left end), yellow = row 0 right end,
    blue = last row left, green = last row right. The text reads mirrored if the panel
    draws mirrored. Note which corner the ribbon cable leaves from.
  - Nibble order: two patches of thin black lines. Patch A is even lines every 3rd pixel
    if the high nibble of a byte is the left pixel; patch B if the low nibble is. The wrong
    patch shows doubled lines every 6th pixel instead (look with a phone camera zoomed in).
    Everything else is drawn in 2-pixel-wide steps, so it looks the same either way.
swatch frame (Task 4 Step 6): six bands of the pure panel colors to photograph in daylight.

Frames are stored run-length encoded (count, value byte pairs; count 1..255) so the header
stays small; firmware/bench/bench.ino expands them. Run from the repo root:
    python tools/make_test_frames.py
It also writes PNG previews (as the panel should look, in the server's nominal palette)."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 480, 720
FRAME_BYTES = W * H // 2

BLACK, WHITE, YELLOW, RED, BLUE, GREEN = 0, 1, 2, 3, 5, 6
CORNER = 96                                   # corner block size, px
# name -> (x0, y0, width, height); x0 even so the 2-pixel bytes line up with the patch
PATCHES = {"A": (60, 330, 160, 110), "B": (260, 330, 160, 110)}
SWATCH_ORDER = [BLACK, WHITE, YELLOW, RED, BLUE, GREEN]
SWATCH_NAMES = {BLACK: "black 0", WHITE: "white 1", YELLOW: "yellow 2",
                RED: "red 3", BLUE: "blue 5", GREEN: "green 6"}
NOMINAL_RGB = {BLACK: (0, 0, 0), WHITE: (255, 255, 255), YELLOW: (255, 255, 0),
               RED: (255, 0, 0), BLUE: (0, 0, 255), GREEN: (0, 255, 0)}


def pack(nibbles: bytes, high_left: bool) -> bytes:
    """Pixels (one nibble value each, row by row) -> packed bytes, two pixels per byte."""
    a, b = nibbles[0::2], nibbles[1::2]
    if not high_left:
        a, b = b, a
    return bytes((x << 4) | y for x, y in zip(a, b))


def unpack(frame: bytes, high_left: bool) -> bytes:
    """Packed bytes -> pixels, read as the panel would with that nibble order."""
    hi = frame.translate(bytes(v >> 4 for v in range(256)))
    lo = frame.translate(bytes(v & 0xF for v in range(256)))
    if not high_left:
        hi, lo = lo, hi
    out = bytearray(len(frame) * 2)
    out[0::2], out[1::2] = hi, lo
    return bytes(out)


def in_patch(x: int, y: int) -> bool:
    return any(x0 <= x < x0 + pw and y0 <= y < y0 + ph for x0, y0, pw, ph in PATCHES.values())


def _font(size: int) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def _text_mask(lines, size=20, gap=6) -> Image.Image:
    """Black-on-white text lines as a 1-bit image, each line (x, y, text[, size])."""
    mask = Image.new("1", (W, H), 1)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"                          # no anti-aliasing: pure black and white
    for item in lines:
        x, y, text = item[:3]
        d.text((x, y), text, fill=0, font=_font(item[3] if len(item) > 3 else size))
    return mask


def _apply_mask_paired(px: bytearray, mask: Image.Image, color: int, region=None) -> None:
    """Paint mask's black pixels in color, widened to whole 2-pixel pairs (so the text looks
    the same whichever nibble is left)."""
    m = mask.load()
    x0, y0, x1, y1 = region or (0, 0, W, H)
    for y in range(y0, y1):
        for x in range(x0 - x0 % 2, x1, 2):
            if m[x, y] == 0 or (x + 1 < W and m[x + 1, y] == 0):
                px[y * W + x] = px[y * W + x + 1] = color


def _rect(px: bytearray, x0, y0, x1, y1, color) -> None:
    for y in range(y0, y1):
        px[y * W + x0:y * W + x1] = bytes([color]) * (x1 - x0)


def corner_frame() -> bytes:
    px = bytearray([WHITE]) * (W * H)
    _rect(px, 0, 0, CORNER, CORNER, RED)
    _rect(px, W - CORNER, 0, W, CORNER, YELLOW)
    _rect(px, 0, H - CORNER, CORNER, H, BLUE)
    _rect(px, W - CORNER, H - CORNER, W, H, GREEN)

    lines = [
        (108, 14, "RED = FIRST BYTE", 22),
        (108, 44, "(row 0, left end)", 18),
        (20, 120, "Which corner is the ribbon cable"),
        (20, 146, "nearest? Note it in RESULTS.md."),
        (20, 186, "If this text reads mirrored,"),
        (20, 212, "the panel draws mirrored."),
        (20, 262, "Nibble order: look at A and B"),
        (20, 288, "with a phone camera zoomed in."),
        (PATCHES["A"][0], 450, "A: high nibble", 18),
        (PATCHES["A"][0], 472, "     = left", 18),
        (PATCHES["B"][0], 450, "B: low nibble", 18),
        (PATCHES["B"][0], 472, "     = left", 18),
        (20, 520, "The right one has even thin lines."),
        (20, 546, "The wrong one has doubled lines."),
        (108, H - 70, "BLUE = last row, left", 18),
        (108, H - 44, "GREEN = last row, right", 18),
    ]
    _apply_mask_paired(px, _text_mask(lines), BLACK)

    for name, (x0, y0, pw, ph) in PATCHES.items():
        # The pattern we want the eye to see: a thin line in every 3rd column.
        want = [BLACK if c % 3 == 0 else WHITE for c in range(pw)]
        # Patch A is right when the high nibble is left: store it as is. Patch B is right when
        # the low nibble is left: store each pixel pair swapped, so reading it low-first undoes it.
        row = want if name == "A" else [want[c ^ 1] for c in range(pw)]
        for y in range(y0, y0 + ph):
            px[y * W + x0:y * W + x0 + pw] = bytes(row)
    return pack(bytes(px), high_left=True)


def swatch_frame() -> bytes:
    px = bytearray([WHITE]) * (W * H)
    band = H // 6
    for i, color in enumerate(SWATCH_ORDER):
        _rect(px, 0, i * band, W, (i + 1) * band, color)
    for i, color in enumerate(SWATCH_ORDER):
        label = _text_mask([(250, i * band + band // 2 - 14, SWATCH_NAMES[color], 26)])
        text_color = WHITE if color in (BLACK, BLUE) else BLACK
        _apply_mask_paired(px, label, text_color, (240, i * band, W, (i + 1) * band))
    return pack(bytes(px), high_left=True)


def rle_encode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        v, n = data[i], 1
        while i + n < len(data) and data[i + n] == v and n < 255:
            n += 1
        out += bytes([n, v])
        i += n
    return bytes(out)


def rle_decode(data: bytes) -> bytes:
    out = bytearray()
    for n, v in zip(data[0::2], data[1::2]):
        out += bytes([v]) * n
    return bytes(out)


def c_array(name: str, data: bytes) -> str:
    rows = [", ".join(f"0x{b:02X}" for b in data[i:i + 16]) for i in range(0, len(data), 16)]
    return f"static const uint8_t {name}[{len(data)}] = {{\n  " + ",\n  ".join(rows) + "\n};\n"


def write_header(path: Path) -> None:
    corner, swatch = rle_encode(corner_frame()), rle_encode(swatch_frame())
    path.write_text(
        "/* Generated by tools/make_test_frames.py; do not edit. Run-length encoded frames:\n"
        " * (count, value) byte pairs, count 1..255, expanding to 172,800 bytes each. */\n"
        "#pragma once\n#include <stdint.h>\n\n"
        + c_array("corner_frame_rle", corner) + "\n" + c_array("swatch_frame_rle", swatch))


def preview(frame: bytes) -> Image.Image:
    img = Image.new("RGB", (W, H))
    img.putdata([NOMINAL_RGB.get(v, (255, 0, 255)) for v in unpack(frame, True)])
    return img


def main() -> None:
    out = ROOT / "firmware" / "bench"
    out.mkdir(parents=True, exist_ok=True)
    write_header(out / "test_frames.h")
    preview(corner_frame()).save(out / "corner_frame.png")
    preview(swatch_frame()).save(out / "swatch_frame.png")
    print(f"wrote {out / 'test_frames.h'} and PNG previews", file=sys.stderr)


if __name__ == "__main__":
    main()
