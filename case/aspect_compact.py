"""Picture shapes in the compact (square-layout) case, to scale: python3 case/aspect_compact.py case/aspect_compact.png
The XIAO sits behind the panel whatever the mask, so the case is the same 64.6 x 96.5 for all."""
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
W, H = 64.6, 96.54
WIN_W, WIN_TOP = 50.6, 96.54 - 3.0 - 0.3 - 2.55 - 0.5
x0 = (W - WIN_W) / 2
opts = [("Full screen (2:3)", 76.04), ("3:4", WIN_W * 4 / 3), ("4:5", WIN_W * 5 / 4), ("Square (1:1)", WIN_W)]
fig, axs = plt.subplots(1, len(opts) + 1, figsize=(15, 5.4))
for ax, (name, ph) in zip(axs, opts):
    ax.add_patch(FancyBboxPatch((0, 0), W, H, boxstyle="round,pad=0,rounding_size=4", fc="#FBFAF7", ec="#15171A", lw=1.4))
    ax.add_patch(Rectangle((x0, WIN_TOP - ph), WIN_W, ph, fc="#5E8C9A", ec="none"))
    ax.add_patch(Rectangle((x0, WIN_TOP - ph), WIN_W, ph * 0.35, fc="#6E8C5A", ec="none"))
    chin = WIN_TOP - ph
    ax.set_title(f"{name}\npicture {WIN_W:.1f} x {ph:.1f}\nchin {chin:.0f} mm ({chin / H:.0%})", fontsize=9)
    ax.set_xlim(-3, 68); ax.set_ylim(-3, 100); ax.set_aspect("equal"); ax.axis("off")
ax = axs[-1]
pw, ph_, pimg = 64.6, 64.6 * 107 / 88, 64.6 * 79 / 88
ax.add_patch(FancyBboxPatch((0, 0), pw, ph_, boxstyle="round,pad=0,rounding_size=4", fc="#FBFAF7", ec="#15171A", lw=1.4))
ax.add_patch(Rectangle(((pw - pimg) / 2, ph_ - 6 * pw / 88 - pimg), pimg, pimg, fc="#5E8C9A", ec="none"))
ax.set_title("Real Polaroid (reference)\nscaled to 64.6 wide\nchin 21%", fontsize=9)
ax.set_xlim(-3, 68); ax.set_ylim(-3, 100); ax.set_aspect("equal"); ax.axis("off")
fig.suptitle("Picture shape in the compact case (64.6 x 96.5 x 6.85), to scale", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.9]); fig.savefig(sys.argv[1], dpi=120)
