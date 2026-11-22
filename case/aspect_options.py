"""Draws picture-aspect options to scale (case/aspect_options.png): python3 case/aspect_options.py case/aspect_options.png.
Exploration for a more Polaroid-like look by masking the bottom of the panel; nothing here is decided."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
W = 64.6
PANEL_H, CLEAR, TOP = 85.64, 0.3, 3.0
AA_TOP, MASK, WIN_W = 2.55, 0.5, 50.6
win_x = (W - WIN_W) / 2
def case(chin_phys):
    H = chin_phys + PANEL_H + 2 * CLEAR + TOP
    win_top = H - TOP - CLEAR - AA_TOP - MASK
    return H, win_top
opts = []
H, wt = case(21.6); opts.append(("Current\n(full screen)", W, H, win_x, wt - 76.04, WIN_W, 76.04))
opts.append(("Square mask,\nsame case", W, H, win_x, wt - WIN_W, WIN_W, WIN_W))
opts.append(("4:5 mask,\nsame case", W, H, win_x, wt - 63.25, WIN_W, 63.25))
H2, wt2 = case(7.6); opts.append(("Square mask +\ncompact chin", W, H2, win_x, wt2 - WIN_W, WIN_W, WIN_W))
pw, ph, pimg = 64.6, 64.6 * 107 / 88, 64.6 * 79 / 88
opts.append(("Real Polaroid\n(scaled to 64.6 wide)", pw, ph, (pw - pimg) / 2, ph - 6 * 64.6 / 88 - pimg, pimg, pimg))
fig, axs = plt.subplots(1, len(opts), figsize=(15, 5.8))
for ax, (name, w, h, x, y, ww, wh) in zip(axs, opts):
    ax.add_patch(FancyBboxPatch((0, 0), w, h, boxstyle="round,pad=0,rounding_size=4", fc="#FBFAF7", ec="#15171A", lw=1.4))
    ax.add_patch(Rectangle((x, y), ww, wh, fc="#5E8C9A", ec="none"))
    ax.add_patch(Rectangle((x, y), ww, wh * 0.35, fc="#6E8C5A", ec="none"))
    chin = y
    ax.set_title(f"{name}\n{w:.1f} x {h:.1f} mm, chin {chin:.0f} ({chin / h:.0%})", fontsize=9)
    ax.set_xlim(-3, 68); ax.set_ylim(-3, 114); ax.set_aspect("equal"); ax.axis("off")
fig.suptitle("Picture aspect options, to scale (chin = bottom edge to picture)", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.9]); fig.savefig(__import__("sys").argv[1], dpi=120)
