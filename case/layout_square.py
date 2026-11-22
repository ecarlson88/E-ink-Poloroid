"""Layout study: square picture (the bottom of the panel masked) with the XIAO standing upright
behind the masked strip, its USB-C end down in a compact chin. Exploration only: the CAD
(case/solidcraft) still models layout v1.

    python3 case/layout_square.py      -> case/layout_square.png

Two ways to mount the XIAO are drawn (side sections):
  A: parts facing the back (as in v1): rear pinhole works; the USB-C needs a back notch.
  B: board flipped, parts facing the front: clean back; USB-C in a pocket under the front
     frame; the buttons face the front, so the pinhole goes in the front of the chin.
Numbers: docs/case-dimensions.md, Erik's measured XIAO (2.8 / 4.4) and XiaoGap 0.75.
Units mm; x right, y up from the case's bottom edge (front view); z from the front face.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

# Parts
PANEL_W, PANEL_H, PANEL_T = 58.0, 85.64, 1.0
AA_W, AA_H, AA_LEFT, AA_TOP = 51.6, 77.04, 3.2, 2.55
FPC_EXIT_W, FPC_TAIL_W, FPC_LEN = 20.256, 26.0, 20.0
ADAPTER_W, ADAPTER_H, ADAPTER_T = 20.647, 35.185, 3.0
BATT_W, BATT_H, BATT_T = 50.0, 34.0, 3.0
XIAO_W, XIAO_L = 17.8, 21.0            # upright: 17.8 across, 21 tall, USB-C at the bottom
XIAO_BODY_T, XIAO_T = 2.8, 4.4          # measured (Erik)
USB_OVERHANG, USB_W, USB_LEN = 1.5, 8.9, 7.3
BTN_FROM_END, BTN_FROM_SIDE = 1.6, 3.0
# Choices (as in v1)
WALL_SIDE, TOP_FRAME, CLEAR, SHELL_WALL, CHIN_WALL = 3.0, 3.0, 0.3, 1.2, 1.2
FRONT_WALL, BACK_WALL, FOLD, MASK = 1.0, 1.0, 2.0, 0.5
XIAO_GAP = 0.75                          # clearance plus wire joints on the pad side (Erik)
MAG_W, MAG_L, MAG_GAP, BOSS_WALL = 3.0, 8.0, 0.2, 1.0
RIB_T, RIB_GAP, CORNER_R = 1.2, 30.0, 4.0

CASE_W = PANEL_W + 2 * (WALL_SIDE + CLEAR)
# The panel sits just above the USB-C body (which ends USB_LEN above the bottom edge).
panel_y = max(USB_LEN + CLEAR, CHIN_WALL + FOLD + CLEAR)
panel_x = WALL_SIDE + CLEAR
CASE_H = panel_y + PANEL_H + CLEAR + TOP_FRAME
aa_x = panel_x + AA_LEFT
win_w = AA_W - 2 * MASK
win_top = panel_y + PANEL_H - AA_TOP - MASK
win = (aa_x + MASK, win_top - win_w, win_w, win_w)          # square
masked = (aa_x, panel_y + PANEL_H - AA_TOP - AA_H, AA_W, (win_top - win_w) - (panel_y + PANEL_H - AA_TOP - AA_H))

# XIAO upright at the right, USB-C face flush with the bottom edge.
xiao_x1 = CASE_W - SHELL_WALL - CLEAR
xiao_x0 = xiao_x1 - XIAO_W
xiao_y0 = USB_OVERHANG
xiao_y1 = xiao_y0 + XIAO_L
usb = (xiao_x0 + (XIAO_W - USB_W) / 2, 0.0, USB_W, USB_LEN)
buttons = [(xiao_x0 + BTN_FROM_SIDE, xiao_y0 + BTN_FROM_END), (xiao_x1 - BTN_FROM_SIDE, xiao_y0 + BTN_FROM_END)]

# Behind the panel, placed relative to it as in v1.
fpc_exit = (panel_x + (PANEL_W - FPC_EXIT_W) / 2, panel_y, FPC_EXIT_W, FPC_LEN - FOLD - 5)
fpc_wide = (panel_x + (PANEL_W - FPC_TAIL_W) / 2, panel_y + FPC_LEN - FOLD - 5, FPC_TAIL_W, 5)
adapter = (panel_x + (PANEL_W - ADAPTER_W) / 2, panel_y + FPC_LEN - FOLD - 3, ADAPTER_W, ADAPTER_H)
batt = (panel_x + (PANEL_W - BATT_W) / 2, adapter[1] + ADAPTER_H + 1.5, BATT_W, BATT_H)
inner_top = CASE_H - SHELL_WALL

# Depth for each mounting (inner depth = front wall's inside face to back wall's inside face).
behind_panel_stack = PANEL_T + XIAO_GAP + XIAO_BODY_T + CLEAR      # same for A and B
panel_batt_stack = PANEL_T + max(BATT_T, ADAPTER_T) + 2 * CLEAR
inner = max(behind_panel_stack, panel_batt_stack)
# A: board's pad side toward the panel; the USB-C top is PANEL_T + XIAO_GAP + XIAO_T from the
#    front wall's inside face, and must not pass the back face (it sits in a back notch).
inner_A = max(inner, PANEL_T + XIAO_GAP + XIAO_T - BACK_WALL)
# B: flipped; pad side toward the back: from the back wall's inside face, XIAO_GAP + XIAO_T to
#    the USB-C top, which may go into a pocket under the front frame (leaving >= 0.5 of frame).
usb_into_front_B = XIAO_GAP + XIAO_T - inner
inner_B = inner if usb_into_front_B <= FRONT_WALL - 0.5 else XIAO_GAP + XIAO_T - (FRONT_WALL - 0.5)
T_A, T_B = FRONT_WALL + inner_A + BACK_WALL, FRONT_WALL + inner_B + BACK_WALL
usb_into_front_B = XIAO_GAP + XIAO_T - inner_B

# Checks.
def overlap(a, b, m=0.0):
    return a[0] < b[0] + b[2] + m and b[0] < a[0] + a[2] + m and a[1] < b[1] + b[3] + m and b[1] < a[1] + a[3] + m

xiao = (xiao_x0, xiao_y0, XIAO_W, XIAO_L)
assert batt[1] + BATT_H <= inner_top - CLEAR, "battery hits the top wall"
assert not overlap(xiao, adapter, CLEAR), "XIAO hits the adapter"
assert usb[1] + USB_LEN + CLEAR <= panel_y + 1e-9, "USB-C under the panel"
fpc_gap_exit = xiao_x0 - (fpc_exit[0] + fpc_exit[2])
fpc_gap_wide = xiao_x0 - (fpc_wide[0] + fpc_wide[2])
fpc_wide_overlaps_xiao_y = fpc_wide[1] < xiao_y1
# Magnet bars: six on the left from above the chin; on the right, above the XIAO.
boss_w, boss_l = MAG_W + MAG_GAP + BOSS_WALL, MAG_L + MAG_GAP + 2 * BOSS_WALL
top_y = CASE_H - CORNER_R - 1.0
bars = []
for side, start in (("L", panel_y + 1.0), ("R", xiao_y1 + CLEAR + 0.5)):
    n = 6 if side == "L" else max(1, int((top_y - start + 4.0) // (boss_l + 4.0)))
    pitch = (top_y - start - boss_l) / max(1, n - 1)
    for i in range(n):
        x = SHELL_WALL if side == "L" else CASE_W - SHELL_WALL - boss_w
        bars.append((x, start + i * pitch, boss_w, boss_l))
for b in bars:
    for name, p in (("battery", batt), ("adapter", adapter), ("XIAO", xiao)):
        assert not overlap(b, p, 0.5), f"magnet pad hits the {name}"
rib_y = panel_y - CLEAR - RIB_T
rib_left = (SHELL_WALL + 1.1, rib_y, CASE_W / 2 - RIB_GAP / 2 - SHELL_WALL - 1.1, RIB_T)
assert rib_y >= CHIN_WALL, "no room for the rib"

# Drawing.
INK, MUTED = "#15171A", "#5C636E"
fig, axs = plt.subplots(1, 3, figsize=(15, 11), gridspec_kw={"width_ratios": [3, 1, 1]})
ax = axs[0]


def box(a, r, label=None, color=INK, ls="-", fill=None, fs=7, lw=1.1, alpha=1.0, hatch=None):
    a.add_patch(Rectangle((r[0], r[1]), r[2], r[3], fill=fill is not None or hatch is not None, facecolor=fill or "none",
                          edgecolor=color, linestyle=ls, lw=lw, alpha=alpha, hatch=hatch))
    if label:
        a.text(r[0] + r[2] / 2, r[1] + r[3] / 2, label, ha="center", va="center", fontsize=fs, color=color)


ax.add_patch(FancyBboxPatch((0, 0), CASE_W, CASE_H, boxstyle=f"round,pad=0,rounding_size={CORNER_R}", fc="#FBFAF7", ec=INK, lw=2))
box(ax, win, None, fill="#5E8C9A")
ax.add_patch(Rectangle((win[0], win[1]), win[2], win[3] * 0.35, fc="#6E8C5A", ec="none"))
ax.text(win[0] + win[2] / 2, win[1] + win[3] - 4, f"picture {win_w:.1f} x {win_w:.1f}", ha="center", va="top", fontsize=9, color="white")
box(ax, masked, f"masked panel strip ({masked[3]:.1f} tall)", color=MUTED, hatch="////", fs=7, alpha=0.6)
box(ax, (panel_x, panel_y, PANEL_W, PANEL_H), color=MUTED, ls="--")
box(ax, batt, f"battery {BATT_W:g} x {BATT_H:g} x {BATT_T:g}", color="#B3261E", ls="--")
box(ax, adapter, "adapter", color="#2457C5", ls="--")
box(ax, fpc_exit, None, color="#B26B00", ls=":", fill="#F6E3B4", alpha=0.5)
box(ax, fpc_wide, None, color="#B26B00", ls=":", fill="#F6E3B4", alpha=0.5)
ax.text(fpc_exit[0] + fpc_exit[2] / 2, panel_y + 3, "panel cable\n(folded behind)", ha="center", fontsize=6, color="#B26B00")
box(ax, xiao, "XIAO\nupright,\nbehind the\nmasked strip", color="#2F8A4E", fill="#D6EEDD", alpha=0.85)
box(ax, usb, None, color="#2F8A4E", fill="#7FBF94")
ax.annotate("USB-C (bottom edge)", (usb[0] + USB_W / 2, 0), (usb[0] + USB_W / 2, -7), ha="center", fontsize=8, color="#2F8A4E",
            arrowprops=dict(arrowstyle="-|>", color="#2F8A4E"))
for bx, by in buttons:
    ax.add_patch(Circle((bx, by), 0.9, fc="#BFE3C9", ec="#2F8A4E"))
ax.annotate("buttons (pinhole: back in A, front in B)", buttons[0], (14, -10.5), fontsize=7, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.7))
for b in bars:
    left = b[0] < CASE_W / 2
    box(ax, (b[0] + (0 if left else BOSS_WALL) + MAG_GAP / 2, b[1] + BOSS_WALL + MAG_GAP / 2, MAG_W, MAG_L), color=MUTED, ls=":")
box(ax, rib_left, None, color=INK, fill="#C9CDD3")
ax.plot([xiao_x0 + 2, 6], [xiao_y1 - 1.5, 3.4], color="#7B3FA0", lw=1.6, ls="--")
ax.text(6, 2.2, "antenna cable down to the chin", fontsize=6, color="#7B3FA0")
for (a0, a1, y, lbl) in ((0, CASE_W, -14, f"{CASE_W:.1f}"),):
    ax.annotate("", (a0, y), (a1, y), arrowprops=dict(arrowstyle="<->", color=INK)); ax.text((a0 + a1) / 2, y - 1, lbl, ha="center", va="top")
ax.annotate("", (-5, 0), (-5, CASE_H), arrowprops=dict(arrowstyle="<->", color=INK))
ax.text(-6, CASE_H / 2, f"{CASE_H:.1f}", rotation=90, ha="right", va="center")
ax.set_title("Front view (parts behind the panel dashed)", fontsize=11)
ax.set_xlim(-12, CASE_W + 6); ax.set_ylim(-19, CASE_H + 4); ax.set_aspect("equal"); ax.axis("off")


def section(a, T, inner_d, mode):
    """Section through the XIAO's middle (x = its centre), front on the left."""
    a.add_patch(Rectangle((0, 0), T, CASE_H, fc="#FFFFFF", ec=INK, lw=2))
    box(a, (FRONT_WALL, panel_y, PANEL_T, PANEL_H), color=MUTED, fill="#DCE6F2")
    if mode == "A":   # pads toward the panel, parts toward the back
        z0 = FRONT_WALL + PANEL_T + XIAO_GAP
        box(a, (z0, xiao_y0, XIAO_BODY_T, XIAO_L), color="#2F8A4E", fill="#D6EEDD")
        box(a, (z0, 0, XIAO_T, USB_LEN), color="#2F8A4E", fill="#7FBF94")
        notch = (T - BACK_WALL - 0.01, -0.01, BACK_WALL + 0.02, USB_LEN + CLEAR)
        a.add_patch(Rectangle(notch[:2], notch[2], notch[3], fc="white", ec="none"))
        a.text(T + 0.8, 4, "back notch\nfor USB-C\n+ rear pinhole", fontsize=7, color="#2F8A4E")
    else:             # flipped: pads toward the back, parts toward the front
        z1 = T - BACK_WALL - XIAO_GAP
        box(a, (z1 - XIAO_BODY_T, xiao_y0, XIAO_BODY_T, XIAO_L), color="#2F8A4E", fill="#D6EEDD")
        box(a, (z1 - XIAO_T, 0, XIAO_T, USB_LEN), color="#2F8A4E", fill="#7FBF94")
        a.text(T + 0.8, 4, f"USB-C {usb_into_front_B:.2f} into\nthe front frame\n+ front pinhole", fontsize=7, color="#2F8A4E")
    box(a, (FRONT_WALL + PANEL_T + CLEAR, adapter[1], ADAPTER_T, ADAPTER_H), color="#2457C5", fill="#DCE4F6")
    box(a, (FRONT_WALL + PANEL_T + CLEAR, batt[1], BATT_T, BATT_H), color="#B3261E", fill="#F6D6D3")
    a.annotate("", (0, -6), (T, -6), arrowprops=dict(arrowstyle="<->", color=INK))
    a.text(T / 2, -7, f"{T:.2f}", ha="center", va="top", fontsize=10)
    a.set_xlim(-3, T + 9); a.set_ylim(-19, CASE_H + 4); a.set_aspect("equal"); a.axis("off")


section(axs[1], T_A, inner_A, "A"); axs[1].set_title("A: parts face the back\n(rear pinhole)", fontsize=10)
section(axs[2], T_B, inner_B, "B"); axs[2].set_title("B: flipped, parts face the front\n(clean back)", fontsize=10)
fig.suptitle(f"Square picture + XIAO behind the masked strip: {CASE_W:.1f} x {CASE_H:.1f} mm, "
             f"{T_A:.2f} (A) or {T_B:.2f} (B) thick", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = Path(__file__).with_name("layout_square.png")
fig.savefig(out, dpi=110)

print(f"case {CASE_W:.1f} x {CASE_H:.2f}; panel bottom at y {panel_y:.1f}; picture {win_w:.1f} square, "
      f"chin (bottom edge to picture) {win[1]:.1f} = {win[1] / CASE_H:.0%}")
print(f"thickness A {T_A:.2f} (USB-C flush in a back notch), B {T_B:.2f} (USB-C {usb_into_front_B:.2f} into the front frame)")
print(f"XIAO x {xiao_x0:.1f}..{xiao_x1:.1f}, y {xiao_y0:.1f}..{xiao_y1:.1f} ({xiao_y1 - panel_y:.1f} behind the panel); "
      f"masked strip {masked[3]:.1f} tall")
print(f"panel cable: narrow part {fpc_gap_exit:.1f} from the XIAO; wide end {fpc_gap_wide:.1f} "
      f"({'overlaps the XIAO in plan: it lies on the panel inside the 0.75 gap' if fpc_wide_overlaps_xiao_y and fpc_gap_wide < 0.3 else 'clear'})")
print(f"battery top {batt[1] + BATT_H:.1f} vs inner top {inner_top:.1f}; magnet bars: {sum(b[0] < CASE_W / 2 for b in bars)} left, "
      f"{sum(b[0] > CASE_W / 2 for b in bars)} right; left rib only")
print(f"wrote {out}")
