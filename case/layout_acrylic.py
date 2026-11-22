"""Acrylic-front case (an additional case type; the v1 and compact cases stay as they are).
A 1 mm acrylic sheet (glass-ready: no holes or pockets) with a white vinyl mask on its back
covers the whole front; one FDM tray holds everything. XIAO in mounting A (parts and buttons
face the back, USB-C flush in a notch through the back wall, rear reset pinhole). Setup button:
a side-actuated switch on the bottom edge of the chin, wired to D5.
Spec: docs/superpowers/specs/2026-11-22-acrylic-front-case-design.md.

    python3 case/layout_acrylic.py     -> case/layout_acrylic.png

Numbers: docs/case-dimensions.md (datasheets), Erik's measured XIAO (2.8 / 4.4).
Units mm; x right, y up from the case's bottom edge (front view); z from the front face.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

# Parts (as in layout_compact.py)
PANEL_W, PANEL_H, PANEL_T = 58.0, 85.64, 1.0
AA_W, AA_H, AA_LEFT, AA_TOP = 51.6, 77.04, 3.2, 2.55
FPC_EXIT_W, FPC_TAIL_W, FPC_LEN = 20.256, 26.0, 20.0
ADAPTER_W, ADAPTER_H, ADAPTER_T = 20.647, 35.185, 3.0
BATT_W, BATT_H, BATT_T = 50.0, 34.0, 3.0
XIAO_W, XIAO_L = 17.8, 21.0            # upright: 17.8 across, 21 tall, USB-C at the bottom
XIAO_BODY_T, XIAO_T = 2.8, 4.4          # measured (Erik)
USB_OVERHANG, USB_W, USB_LEN = 1.5, 8.9, 7.3
BTN_FROM_END, BTN_FROM_SIDE = 1.6, 3.0
SW_W, SW_D, SW_T = 3.5, 2.9, 1.6        # side-actuated switch: placeholder until the part is chosen
PLUNGER_W, PLUNGER_H = 1.6, 1.0         # plunger slot through the bottom wall (placeholder)
# Choices
SHEET_T, MASK_T = 1.0, 0.1              # acrylic sheet; vinyl mask on its back
WALL, BACK_WALL, CLEAR, FOLD, MASK = 1.2, 1.0, 0.3, 2.0, 0.5
PIC_RATIO = 4 / 3
XIAO_GAP = 0.65                         # Ruling: 0.75 less the mask's 0.1; joint room stays 0.45
JOINT = 0.45                            # battery wire joints on the XIAO's pads (as compact)
JOINT_CLEAR = 0.2                       # joints to the panel's back (compact: 0.3; the mask took 0.1)
BATT_GAP = 1.0                          # adapter to battery (compact: 1.5)
SW_X = 12.0                             # switch centre
LEDGE_T = 0.8                           # chin ledge under the sheet (bonding area)
MAG_W, MAG_L, MAG_GAP, BOSS_WALL, MAG_PROUD = 3.0, 8.0, 0.2, 1.0, 0.4
RIB_T, RIB_GAP, CORNER_R = 1.2, 30.0, 4.0
PIN_D = 1.2

CASE_W = PANEL_W + 2 * (CLEAR + WALL)
panel_x = WALL + CLEAR
panel_y = max(USB_LEN + CLEAR, WALL + FOLD + CLEAR)
CASE_H = panel_y + PANEL_H + CLEAR + WALL
INNER = max(MASK_T + PANEL_T + BATT_T + 2 * CLEAR,
            MASK_T + PANEL_T + XIAO_GAP + XIAO_BODY_T + CLEAR,
            MASK_T + PANEL_T + XIAO_GAP + XIAO_T - BACK_WALL)
T = SHEET_T + INNER + BACK_WALL
z_back_in = SHEET_T + INNER                         # inside face of the back wall

# Picture window (mask), as in the compact case
aa_x = panel_x + AA_LEFT
win_w = AA_W - 2 * MASK
win_top = panel_y + PANEL_H - AA_TOP - MASK
win_h = win_w * PIC_RATIO
win = (aa_x + MASK, win_top - win_h, win_w, win_h)
masked = (aa_x, panel_y + PANEL_H - AA_TOP - AA_H, AA_W, win[1] - (panel_y + PANEL_H - AA_TOP - AA_H))

# XIAO upright at the right, USB-C face flush with the bottom edge
xiao_x1 = CASE_W - WALL - CLEAR
xiao_x0 = xiao_x1 - XIAO_W
xiao_y0, xiao_y1 = USB_OVERHANG, USB_OVERHANG + XIAO_L
xiao = (xiao_x0, xiao_y0, XIAO_W, XIAO_L)
usb = (xiao_x0 + (XIAO_W - USB_W) / 2, 0.0, USB_W, USB_LEN)
notch = (usb[0] - CLEAR, -1.0, USB_W + 2 * CLEAR, USB_LEN + CLEAR + 1.0)
pin = (xiao_x1 - BTN_FROM_SIDE, xiao_y0 + BTN_FROM_END)       # mounting A: mirror of B's front pinhole
z_pads = SHEET_T + MASK_T + PANEL_T + XIAO_GAP                 # XIAO underside (pads, joints toward the front)

# Behind the panel (as in the compact layout)
fold = (panel_x + (PANEL_W - FPC_EXIT_W) / 2, panel_y - FOLD, FPC_EXIT_W, FOLD)
fpc_exit = (panel_x + (PANEL_W - FPC_EXIT_W) / 2, panel_y, FPC_EXIT_W, FPC_LEN - FOLD - 5)
fpc_wide = (panel_x + (PANEL_W - FPC_TAIL_W) / 2, panel_y + FPC_LEN - FOLD - 5, FPC_TAIL_W, 5)
adapter = (panel_x + (PANEL_W - ADAPTER_W) / 2, panel_y + FPC_LEN - FOLD - 3, ADAPTER_W, ADAPTER_H)
batt = (panel_x + (PANEL_W - BATT_W) / 2, adapter[1] + ADAPTER_H + BATT_GAP, BATT_W, BATT_H)
inner_top = CASE_H - WALL

# Edge switch, its backstop rib, the chin ledge and the left cross rib
switch = (SW_X - SW_W / 2, WALL, SW_W, SW_D)
backstop = (SW_X - SW_W / 2 - 1.0, WALL + SW_D, SW_W + 2.0, RIB_T)
ledge_top = panel_y - FOLD - CLEAR
ledge = (WALL, WALL, CASE_W - 2 * WALL, ledge_top - WALL)
rib = (WALL, panel_y - CLEAR - RIB_T, CASE_W / 2 - RIB_GAP / 2 - WALL, RIB_T)

# Magnet bars: six on the left from above the chin; on the right, above the XIAO
boss_w, boss_l = MAG_W + MAG_GAP + BOSS_WALL, MAG_L + MAG_GAP + 2 * BOSS_WALL
top_y = CASE_H - CORNER_R - 1.0
bars = []
for side, start in (("L", panel_y + 1.0), ("R", xiao_y1 + CLEAR + 0.5)):
    n = 6 if side == "L" else max(1, int((top_y - start + 4.0) // (boss_l + 4.0)))
    pitch = (top_y - start - boss_l) / max(1, n - 1)
    for i in range(n):
        x = WALL if side == "L" else CASE_W - WALL - boss_w
        bars.append((x, start + i * pitch, boss_w, boss_l))


def overlap(a, b, m=0.0):
    return a[0] < b[0] + b[2] + m and b[0] < a[0] + a[2] + m and a[1] < b[1] + b[3] + m and b[1] < a[1] + a[3] + m


# Checks
assert abs(T - 7.15) < 0.01, f"thickness {T:.2f}, not 7.15"
assert z_pads + XIAO_T <= T + 1e-9, "USB-C sticks out of the back"
assert z_pads - JOINT - JOINT_CLEAR >= SHEET_T + MASK_T + PANEL_T - 1e-9, "XIAO joints hit the panel"
for name, part in (("XIAO", xiao), ("USB-C notch", notch), ("cable fold", fold)):
    assert not overlap(switch, part, CLEAR), f"switch hits the {name}"
    assert not overlap(backstop, part, CLEAR), f"switch backstop hits the {name}"
assert not overlap(backstop, rib, CLEAR), "switch backstop hits the cross rib"
ledge_room = MASK_T + PANEL_T + XIAO_GAP - LEDGE_T
assert ledge_room >= JOINT + CLEAR - 1e-9, "no room for the XIAO joints under the ledge"
assert ledge_top <= panel_y - FOLD - CLEAR + 1e-9, "ledge reaches the cable fold"
assert SHEET_T + LEDGE_T <= z_back_in - SW_T - CLEAR, "ledge hits the switch"
batt_back_gap = INNER - (MASK_T + PANEL_T + CLEAR + BATT_T)
for b in bars:
    for name, p in (("adapter", adapter), ("XIAO", xiao)):
        assert not overlap(b, p, 0.5), f"magnet pad hits the {name}"
    if overlap(b, batt, 0.5):
        assert batt_back_gap >= MAG_PROUD + CLEAR - 1e-9, "magnet pad under the battery without depth to spare"
assert batt[1] + BATT_H <= inner_top - CLEAR + 1e-9, "battery hits the top wall"
assert rib[0] + rib[2] <= fold[0] - CLEAR, "rib hits the cable fold"
assert not overlap(xiao, adapter, CLEAR), "XIAO hits the adapter"

# Drawing
INK, MUTED = "#15171A", "#5C636E"
RED, BLUE, GREEN, ORANGE, PURPLE = "#B3261E", "#2457C5", "#2F8A4E", "#B26B00", "#7B3FA0"
fig, axs = plt.subplots(1, 2, figsize=(13, 11), gridspec_kw={"width_ratios": [3, 1.3]})


def box(a, r, label=None, color=INK, ls="-", fill=None, fs=7, lw=1.1, alpha=1.0, hatch=None):
    a.add_patch(Rectangle((r[0], r[1]), r[2], r[3], fill=fill is not None or hatch is not None, facecolor=fill or "none",
                          edgecolor=color, linestyle=ls, lw=lw, alpha=alpha, hatch=hatch))
    if label:
        a.text(r[0] + r[2] / 2, r[1] + r[3] / 2, label, ha="center", va="center", fontsize=fs, color=color)


ax = axs[0]
ax.add_patch(FancyBboxPatch((0, 0), CASE_W, CASE_H, boxstyle=f"round,pad=0,rounding_size={CORNER_R}", fc="#FBFAF7", ec=INK, lw=2))
box(ax, win, None, fill="#5E8C9A")
ax.add_patch(Rectangle((win[0], win[1]), win[2], win[3] * 0.35, fc="#6E8C5A", ec="none"))
ax.text(win[0] + win[2] / 2, win[1] + win[3] - 4, f"picture {win_w:.1f} x {win_h:.1f} (3:4)\nclear window in the vinyl mask",
        ha="center", va="top", fontsize=9, color="white")
box(ax, masked, f"masked panel strip ({masked[3]:.1f})", color=MUTED, hatch="////", fs=7, alpha=0.6)
box(ax, (panel_x, panel_y, PANEL_W, PANEL_H), color=MUTED, ls="--")
box(ax, batt, f"battery {BATT_W:g} x {BATT_H:g} x {BATT_T:g}", color=RED, ls="--")
box(ax, adapter, "adapter", color=BLUE, ls="--")
for r in (fpc_exit, fpc_wide):
    box(ax, r, None, color=ORANGE, ls=":", fill="#F6E3B4", alpha=0.5)
box(ax, fold, None, color=ORANGE, ls=":", fill="#F6E3B4", alpha=0.8)
box(ax, xiao, "XIAO\nupright,\nparts face\nthe back\n(mounting A)", color=GREEN, fill="#D6EEDD", alpha=0.85)
box(ax, usb, None, color=GREEN, fill="#7FBF94")
ax.annotate("USB-C, flush in a\nback-wall notch", (usb[0] + USB_W / 2, 0), (usb[0] + USB_W / 2, -8), ha="center", fontsize=7,
            color=GREEN, arrowprops=dict(arrowstyle="-|>", color=GREEN))
ax.add_patch(Circle(pin, PIN_D / 2, fc="white", ec=INK))
ax.annotate("rear reset pinhole", pin, (CASE_W + 1, 10), fontsize=7, color=INK, arrowprops=dict(arrowstyle="-", color=INK, lw=0.7))
box(ax, ledge, None, color=PURPLE, ls=":", fill="#EADCF3", alpha=0.45)
ax.text(24, WALL + 0.4, f"chin ledge under the sheet ({ledge[3]:.1f} x {LEDGE_T:g}): tape area", fontsize=6, color=PURPLE)
box(ax, switch, None, color=INK, fill="#C9CDD3")
box(ax, backstop, None, color=INK, fill="#8E949C")
ax.add_patch(Rectangle((SW_X - PLUNGER_W / 2, 0), PLUNGER_W, WALL, fc="white", ec=INK))
ax.annotate("setup button (D5), pressed\nupward from the bottom edge", (SW_X, 0), (SW_X - 8, -8), fontsize=7, color=INK,
            arrowprops=dict(arrowstyle="-|>", color=INK))
box(ax, rib, None, color=INK, fill="#C9CDD3")
for b in bars:
    left = b[0] < CASE_W / 2
    box(ax, (b[0] + (0 if left else BOSS_WALL) + MAG_GAP / 2, b[1] + BOSS_WALL + MAG_GAP / 2, MAG_W, MAG_L), color=MUTED, ls=":")
ax.annotate("", (0, -13), (CASE_W, -13), arrowprops=dict(arrowstyle="<->", color=INK))
ax.text(CASE_W / 2, -14, f"{CASE_W:.1f}", ha="center", va="top", fontsize=10)
ax.annotate("", (-5, 0), (-5, CASE_H), arrowprops=dict(arrowstyle="<->", color=INK))
ax.text(-6, CASE_H / 2, f"{CASE_H:.1f}", rotation=90, ha="right", va="center", fontsize=10)
ax.set_title("Front view through the sheet (parts behind dashed)", fontsize=11)
ax.set_xlim(-12, CASE_W + 14); ax.set_ylim(-18, CASE_H + 4); ax.set_aspect("equal"); ax.axis("off")

# Section through the XIAO's middle, front on the left
a = axs[1]
a.add_patch(Rectangle((0, 0), T, CASE_H, fc="#FFFFFF", ec=INK, lw=2))
box(a, (0, 0, SHEET_T, CASE_H), None, color=BLUE, fill="#E4EEF9")
box(a, (SHEET_T, 0, MASK_T, CASE_H), None, color=MUTED, fill="#FFFFFF")
box(a, (SHEET_T + MASK_T, panel_y, PANEL_T, PANEL_H), color=MUTED, fill="#DCE6F2")
box(a, (SHEET_T, WALL, LEDGE_T, ledge[3]), None, color=PURPLE, fill="#EADCF3")
box(a, (z_pads, xiao_y0, XIAO_BODY_T, XIAO_L), color=GREEN, fill="#D6EEDD")
box(a, (z_pads, 0, XIAO_T, USB_LEN), color=GREEN, fill="#7FBF94")
a.add_patch(Rectangle((T - BACK_WALL - 0.01, -0.01), BACK_WALL + 0.02, USB_LEN + CLEAR, fc="white", ec="none"))
box(a, (SHEET_T + MASK_T + PANEL_T + CLEAR, batt[1], BATT_T, BATT_H), color=RED, fill="#F6D6D3")
box(a, (SHEET_T + MASK_T + PANEL_T + CLEAR, adapter[1], ADAPTER_T, ADAPTER_H), color=BLUE, fill="#DCE4F6")
a.text(T + 0.6, 3.5, "USB-C notch\n+ rear pinhole", fontsize=7, color=GREEN)
a.text(-0.3, CASE_H - 6, "acrylic\n+ mask", fontsize=7, color=BLUE, ha="right")
a.annotate("", (0, -13), (T, -13), arrowprops=dict(arrowstyle="<->", color=INK))
a.text(T / 2, -14, f"{T:.2f}", ha="center", va="top", fontsize=10)
a.set_xlim(-6, T + 8); a.set_ylim(-18, CASE_H + 4); a.set_aspect("equal"); a.axis("off")
a.set_title("Section through the XIAO\n(front left)", fontsize=10)

chin = win[1]
fig.suptitle(f"Acrylic-front case, 3:4 picture, mounting A: {CASE_W:.1f} x {CASE_H:.1f} x {T:.2f} mm "
             f"(compact today: 64.6 x 96.5 x 6.85)", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = Path(__file__).with_name("layout_acrylic.png")
fig.savefig(out, dpi=110)

print(f"case {CASE_W:.1f} x {CASE_H:.2f} x {T:.2f}; inner depth {INNER:.2f}; picture {win_w:.1f} x {win_h:.1f}, "
      f"chin (bottom edge to picture) {chin:.1f} = {chin / CASE_H:.0%}, side border {win[0]:.1f}")
print(f"XIAO x {xiao_x0:.1f}..{xiao_x1:.1f}, y {xiao_y0:.1f}..{xiao_y1:.1f}; rear pinhole at ({pin[0]:.1f}, {pin[1]:.1f})")
print(f"switch centre x {SW_X:g}, body {SW_W:g} x {SW_D:g} x {SW_T:g}; ledge {ledge[2]:.1f} x {ledge[3]:.1f} x {LEDGE_T:g}, "
      f"room under it for joints {ledge_room:.2f}")
print(f"battery-to-back-wall gap {batt_back_gap:.2f} (bosses stand {MAG_PROUD:g} proud); battery top {batt[1] + BATT_H:.2f} "
      f"vs inner top {inner_top:.2f}; magnet bars: {sum(b[0] < CASE_W / 2 for b in bars)} left, {sum(b[0] > CASE_W / 2 for b in bars)} right")
print(f"wrote {out}")
