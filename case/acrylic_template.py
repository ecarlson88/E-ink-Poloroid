"""Printable 1:1 template for hand-cutting and painting the acrylic front (acrylic-front case).
Reads the sheet and window sizes from case/solidcraft/acrylic_sheet.svg (written by
`build_case.py acrylic`), so it always matches the CAD.

    python3 case/acrylic_template.py     -> case/acrylic_template.pdf (US Letter; also fits A4) and .png

Print at 100% / "Actual size" (not "Fit to page"), then check both 50 mm scale bars.
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = Path(__file__).parent
svg = (HERE / "solidcraft" / "acrylic_sheet.svg").read_text()
rects = [dict(re.findall(r'([\w-]+)="([-\d.]+)"', r)) for r in re.findall(r"<rect ([^>]*)/>", svg)]
sheet, window = ({k: float(v) for k, v in r.items() if k in ("x", "y", "width", "height")} for r in rects)
SW, SH = sheet["width"], sheet["height"]
WX, WY_TOP, WW, WH = window["x"], window["y"], window["width"], window["height"]   # y from the sheet's top
WY = SH - WY_TOP - WH                                                               # y from the bottom

PAGE_W, PAGE_H = 215.9, 279.4        # US Letter, mm; everything stays inside A4 (210 x 297) too
MM = 1 / 25.4
fig = plt.figure(figsize=(PAGE_W * MM, PAGE_H * MM))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, PAGE_W); ax.set_ylim(0, PAGE_H); ax.set_aspect("equal"); ax.axis("off")
INK, GREY, BLUE = "#000000", "#777777", "#1f4fbf"


def text(x, y, s, **kw):
    ax.text(x, y, s, fontsize=kw.pop("fs", 8), color=kw.pop("color", INK), **kw)


def scale_bar(x, y, vertical=False):
    L = 50.0
    if vertical:
        ax.plot([x, x], [y, y + L], color=INK, lw=0.8)
        for t in range(0, 51, 10):
            ax.plot([x - (1.5 if t % 50 == 0 else 0.8), x], [y + t, y + t], color=INK, lw=0.6)
        text(x - 2.5, y + L / 2, "50 mm", ha="right", va="center", rotation=90, fs=7)
    else:
        ax.plot([x, x + L], [y, y], color=INK, lw=0.8)
        for t in range(0, 51, 10):
            ax.plot([x + t, x + t], [y, y - (1.5 if t % 50 == 0 else 0.8)], color=INK, lw=0.6)
        text(x + L / 2, y - 2.5, "50 mm", ha="center", va="top", fs=7)


# Header
text(15, 265, "Acrylic front: cutting and paint-mask template", fs=12, weight="bold")
text(15, 258, "Print at 100% / Actual size (not Fit to page). Both scale bars must measure exactly 50 mm.", fs=8)

# 1. Sheet template
X0, Y0 = 20.0, 140.0
ax.add_patch(Rectangle((X0, Y0), SW, SH, fill=False, ec=INK, lw=0.6))
ax.add_patch(Rectangle((X0 + WX, Y0 + WY), WW, WH, fill=True, fc="#e8eefb", ec=BLUE, lw=0.6, ls="--"))
for cx, cy in ((X0, Y0), (X0 + SW, Y0), (X0, Y0 + SH), (X0 + SW, Y0 + SH)):   # corner ticks outside the line
    sx = -1 if cx == X0 else 1
    sy = -1 if cy == Y0 else 1
    ax.plot([cx + sx * 1.0, cx + sx * 4.0], [cy, cy], color=INK, lw=0.4)
    ax.plot([cx, cx], [cy + sy * 1.0, cy + sy * 4.0], color=INK, lw=0.4)
text(X0 + SW / 2, Y0 + WY + WH / 2, f"clear window\n{WW:.1f} x {WH:.1f}\n(do not paint)", ha="center", va="center",
     fs=8, color=BLUE)
text(X0 + SW / 2, Y0 + SH + 1.5, "TOP (away from the panel cable)", ha="center", va="bottom", fs=7)
text(X0 + SW / 2, Y0 + WY / 2, "chin: paint", ha="center", va="center", fs=8, color=GREY)
text(X0 + SW / 2, Y0 - 6, f"1. Sheet: {SW:.1f} x {SH:.2f} mm, square corners", ha="center", va="top", fs=8, weight="bold")
text(X0 + SW / 2, Y0 - 10, "cut 1 mm acrylic on the solid line", ha="center", va="top", fs=7)
# window offsets
text(X0 + SW + 6, Y0 + SH - 2, f"Window position on the sheet:\n  {WX:.2f} mm from the left and right edges\n"
     f"  {WY_TOP:.2f} mm from the top edge\n  {WY:.2f} mm from the bottom edge", va="top", fs=7.5)

# 2. Window paint mask
MX, MY = 112.0, 140.0
ax.add_patch(Rectangle((MX, MY), WW, WH, fill=False, ec=BLUE, lw=0.6))
text(MX + WW / 2, MY + WH / 2, f"2. Paint mask\n{WW:.1f} x {WH:.2f} mm\n\ncut from painter's tape\nor vinyl on this line",
     ha="center", va="center", fs=8, color=BLUE)

# Notes
notes = [
    "How to use",
    "a. Cut the sheet (1) a hair outside the line, then sand or file the edges until it drops into the tray's lip",
    f"    (the pocket is {SW + 0.3:.1f} x {SH + 0.3:.2f}: 0.15 mm of play per side). Keep the corners square.",
    "b. Peel the film from the back face only. Lay the sheet over this page, back face up, and stick the",
    "    paint mask (2) inside the dashed window. Burnish its edges so paint can't creep under.",
    "c. Paint the back face (the face toward the panel), in thin coats. Peel the mask before the last coat",
    "    is fully hard for a clean edge. Keep the front film on until assembly.",
    "d. Use a paint made for plastics, and test it on an offcut first: some solvent paints craze acrylic.",
    "    Let it cure fully (days, not hours) before assembly: fumes near the panel are bad (its datasheet",
    "    warns against acetic-acid and chlorine materials).",
    "The window is the same distance from both sides, so the back face can go either way left-right;",
    "only top and bottom matter. Sizes come from case/solidcraft/acrylic_sheet.svg.",
]
for i, line in enumerate(notes):
    text(15, 118 - i * 5.0, line, fs=8.5 if i else 9.5, weight="bold" if i == 0 else "normal")

scale_bar(135, 30)
scale_bar(200, 25, vertical=True)

out = HERE / "acrylic_template.pdf"
fig.savefig(out)
fig.savefig(out.with_suffix(".png"), dpi=150)
print(f"sheet {SW:.2f} x {SH:.2f}; window {WW:.2f} x {WH:.2f} at {WX:.2f} from the sides, {WY_TOP:.2f} from the top; wrote {out}")
