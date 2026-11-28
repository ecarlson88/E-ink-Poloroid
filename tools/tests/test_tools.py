"""Tests for the frame tools. Run from the repo root: pytest tools"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "server"))

import make_setup_screen  # noqa: E402
import make_test_frames as tf  # noqa: E402
import imaging  # noqa: E402

W, H, FRAME = 480, 720, 172_800
PALETTE_NIBBLES = {0, 1, 2, 3, 5, 6}


def _header_bytes(text: str, name: str) -> bytes:
    body = re.search(r"%s\[(\d+)\]\s*=\s*\{(.*?)\};" % name, text, re.S)
    assert body, f"no array {name}"
    values = re.findall(r"0x([0-9A-Fa-f]{2})", body.group(2))
    assert int(body.group(1)) == len(values)
    return bytes(int(v, 16) for v in values)


# --- packing ------------------------------------------------------------------------------

def test_pack_unpack_round_trip_both_orders():
    nib = bytes([0, 1, 2, 3, 5, 6] * 2)
    assert tf.pack(nib, high_left=True)[:3] == bytes([0x01, 0x23, 0x56])
    assert tf.pack(nib, high_left=False)[:3] == bytes([0x10, 0x32, 0x65])
    for hl in (True, False):
        assert tf.unpack(tf.pack(nib, hl), hl) == nib


def test_pack_matches_server_imaging():
    """The tool's 'high nibble is left' is the server's HIGH_NIBBLE_IS_LEFT = True."""
    img = imaging.frame_to_image(tf.pack(bytes([3, 1] * (W * H // 2)), imaging.HIGH_NIBBLE_IS_LEFT))
    assert img.getpixel((0, 0)) == imaging.PALETTE[3]
    assert img.getpixel((1, 0)) == imaging.PALETTE[1]


# --- corner test frame (Task 1 Step 4) -----------------------------------------------------

def test_corner_frame_size_and_colors():
    f = tf.corner_frame()
    assert len(f) == FRAME
    nib = tf.unpack(f, True)
    assert set(nib) <= PALETTE_NIBBLES
    px = lambda x, y: nib[y * W + x]
    assert px(0, 0) == tf.RED and px(W - 1, 0) == tf.YELLOW
    assert px(0, H - 1) == tf.BLUE and px(W - 1, H - 1) == tf.GREEN


def test_corner_frame_is_nibble_order_proof_outside_the_patches():
    """Everything but the two nibble patches looks the same whichever nibble is left, so
    the corners and text read the same either way and only the patches differ."""
    f = tf.corner_frame()
    for y in range(H):
        for xb in range(W // 2):
            if tf.in_patch(2 * xb, y):
                continue
            b = f[y * (W // 2) + xb]
            assert b >> 4 == b & 0xF, (2 * xb, y)


def test_corner_frame_patches_tell_the_order_apart():
    """Patch A is even fine lines (every 3rd column) if the high nibble is left; patch B if
    the low nibble is left. The wrong one shows double lines every 6th column."""
    f = tf.corner_frame()
    for name, high_left in (("A", True), ("B", False)):
        x0, y0, pw, ph = tf.PATCHES[name]
        right = tf.unpack(f, high_left)
        wrong = tf.unpack(f, not high_left)
        y = y0 + ph // 2
        cols_right = [x - x0 for x in range(x0, x0 + pw) if right[y * W + x] == tf.BLACK]
        cols_wrong = [x - x0 for x in range(x0, x0 + pw) if wrong[y * W + x] == tf.BLACK]
        assert cols_right == [c for c in range(pw) if c % 3 == 0], name
        assert any(b - a == 1 for a, b in zip(cols_wrong, cols_wrong[1:])), name  # pairs


# --- swatch frame (Task 4 Step 6) ----------------------------------------------------------

def test_swatch_frame_has_six_bands():
    f = tf.swatch_frame()
    assert len(f) == FRAME
    nib = tf.unpack(f, True)
    assert set(nib) == PALETTE_NIBBLES
    assert all(b >> 4 == b & 0xF for b in f)  # nibble-order proof
    # the left edge of each band is its pure color
    band = H // 6
    for i, color in enumerate(tf.SWATCH_ORDER):
        assert nib[(i * band + band // 2) * W + 2] == color


# --- RLE for the bench header ---------------------------------------------------------------

def test_rle_round_trip_and_small():
    for f in (tf.corner_frame(), tf.swatch_frame()):
        enc = tf.rle_encode(f)
        assert tf.rle_decode(enc) == f
        assert len(enc) < 80_000   # flash is 8 MB; the line patches do not compress


def test_bench_header(tmp_path):
    out = tmp_path / "test_frames.h"
    tf.write_header(out)
    text = out.read_text()
    assert tf.rle_decode(_header_bytes(text, "corner_frame_rle")) == tf.corner_frame()
    assert tf.rle_decode(_header_bytes(text, "swatch_frame_rle")) == tf.swatch_frame()


# --- setup screen (Task 5 Step 3) ----------------------------------------------------------

def test_setup_screen_frame():
    f = make_setup_screen.setup_screen_frame()
    assert len(f) == FRAME
    nib = tf.unpack(f, imaging.HIGH_NIBBLE_IS_LEFT)
    assert set(nib) <= {0, 1}                     # black text on white
    assert nib.count(0) > 2000                    # there is text


def test_setup_screen_header_has_exactly_one_frame(tmp_path):
    out = tmp_path / "setup_screen.h"
    make_setup_screen.write_header(out)
    data = _header_bytes(out.read_text(), "setup_screen_frame")
    assert len(data) == FRAME
    assert data == make_setup_screen.setup_screen_frame()


def test_committed_headers_are_current():
    """Regenerate with the tools if this fails (python tools/make_setup_screen.py, ...)."""
    setup = ROOT / "firmware/magnet/setup_screen.h"
    assert _header_bytes(setup.read_text(), "setup_screen_frame") == make_setup_screen.setup_screen_frame()
    bench = (ROOT / "firmware/bench/test_frames.h").read_text()
    assert tf.rle_decode(_header_bytes(bench, "corner_frame_rle")) == tf.corner_frame()
