"""Layout v0 for the magnet case: a to-scale front view and side section.

Every number is a parameter below, taken from docs/case-dimensions.md
(datasheets, unmeasured). Change them after measuring and rerun:
    python3 case/layout.py      -> case/layout_v0.png
Units: mm. Origin: bottom-left outer corner of the case, front view.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

# --- Parts (datasheets; measure and update) ---
PANEL_W, PANEL_H, PANEL_T = 58.0, 85.64, 1.0
# Active area per the datasheet DRAWING (the table says 50.4 x 75.6): margins from panel edges
AA_LEFT, AA_RIGHT, AA_TOP = 3.2, 3.2, 2.55
AA_W, AA_H = 51.6, 77.04
FPC_EXIT_W, FPC_TAIL_W, FPC_LEN = 20.256, 26.0, 20.0
ADAPTER_W, ADAPTER_H, ADAPTER_T = 20.647, 35.185, 3.0   # thickness unknown (header removed); guess
BATT_W, BATT_H, BATT_T = 50.0, 34.0, 3.0                # 303450, lying sideways
XIAO_W, XIAO_H, XIAO_T = 21.0, 17.8, 4.46               # underside to top of the USB-C (STEP model)
XIAO_BODY_T = 3.25                                       # underside to top of the shield can, no USB-C (STEP; Erik estimates ~2)
USB_OVERHANG, USB_W, USB_LEN = 1.5, 8.9, 7.3
BTN_FROM_END, BTN_FROM_SIDE, BTN_W, BTN_H, BTN_TOP = 1.6, 3.0, 1.6, 2.6, 0.73  # R and B buttons (STEP): centre from USB end / long edge, size, height above the PCB
PCB_T = 1.25
PINHOLE_D = 1.2                                          # for a straightened paperclip
JOINT = 1.0                                              # battery wire solder joints on the underside pads (guess)

# --- Case choices (v0 proposals) ---
WALL_SIDE, WALL_TOP = 3.0, 3.0      # frame width around the panel at the sides and top
CLEAR = 0.3                          # gap around each part
FOLD = 2.0                           # room under the panel for the FPC's fold
CHIN_WALL = 1.2
FRONT_WALL, BACK_WALL = 1.0, 1.0
# Magnet option: "bars" (8 x 3 x 1, upright along the side walls) or "discs" (Erik's own 8 mm discs,
# measured 0.6 thick: flush with the inside of the back wall, so they can go anywhere).
MAG_STYLE = sys.argv[1] if len(sys.argv) > 1 else "bars"
MAG_W, MAG_L = 3.0, 8.0
MAG_D = 8.0
MAGNET_T = 1.0 if MAG_STYLE == "bars" else 0.6
MAG_PER_SIDE = 6
MAG_GAP, BOSS_WALL = 0.2, 1.0
SHELL_WALL, CORNER_R = 1.2, 4.0          # back shell side wall and outer corner radius (as in the CAD)
MAGNET_SKIN, MAGNET_CAP = 0.4, 0.0   # Erik: pocket open on the inside, 0.4 skin on the fridge side, magnet glued in
MAGNET_CLEAR = 0.5                   # keep each magnet's boss this far from any part
MASK = 0.5                           # the frame overlaps the active area by this much per side
# XIAO mounted upside down (Erik): underside pads and wire joints face the front wall, parts face
# the back; the USB-C sits in a notch through the back shell, so only the board body sets the depth.

inner_depth = max(PANEL_T + max(BATT_T, ADAPTER_T), JOINT + XIAO_BODY_T) + 2 * CLEAR
CASE_W = PANEL_W + 2 * (WALL_SIDE + CLEAR)
CHIN_H = FOLD + XIAO_H + 2 * CLEAR + CHIN_WALL
CASE_H = CHIN_H + PANEL_H + 2 * CLEAR + WALL_TOP
CASE_T = FRONT_WALL + inner_depth + BACK_WALL

panel_x, panel_y = WALL_SIDE + CLEAR, CHIN_H + CLEAR
aa_x, aa_y = panel_x + AA_LEFT, panel_y + PANEL_H - AA_TOP - AA_H
win = (aa_x + MASK, aa_y + MASK, AA_W - 2 * MASK, AA_H - 2 * MASK)

fpc_top_behind = panel_y + FPC_LEN - FOLD           # where the folded tail ends, behind the panel
adapter_x = panel_x + (PANEL_W - ADAPTER_W) / 2
adapter_y = fpc_top_behind - 3.0                     # connector lip at the bottom of the board
batt_x = panel_x + (PANEL_W - BATT_W) / 2
batt_y = adapter_y + ADAPTER_H + 1.5
xiao_x = CASE_W - USB_OVERHANG - XIAO_W   # USB-C face flush with the outside of the right wall
xiao_y = CHIN_WALL + CLEAR + (CHIN_H - FOLD - CHIN_WALL - 2 * CLEAR - XIAO_H) / 2

# Magnets sit in pockets in the back wall: each needs a boss MAGNET_SKIN + MAGNET_T + MAGNET_CAP
# thick, so it pokes (that - BACK_WALL) into the cavity and must sit clear of every part behind it.
# Bars stand upright against the side walls (the wall is one side of the pocket), from just above
# the chin to just below the rounded top corners.
boss = MAGNET_SKIN + MAGNET_T + MAGNET_CAP - BACK_WALL
boss_w = MAG_W + MAG_GAP + BOSS_WALL            # from the wall inward
boss_l = MAG_L + MAG_GAP + 2 * BOSS_WALL
mag_bottom = panel_y + 1.0
mag_top = CASE_H - CORNER_R - 1.0
pitch = (mag_top - mag_bottom - boss_l) / (MAG_PER_SIDE - 1)
BOSSES = []                                        # (x, y, w, h) of each raised pad (bars only)
DISCS = []                                         # (cx, cy) of each flush disc pocket
if MAG_STYLE == "bars":
    for i in range(MAG_PER_SIDE):
        y = mag_bottom + i * pitch
        BOSSES.append((SHELL_WALL, y, boss_w, boss_l))
        BOSSES.append((CASE_W - SHELL_WALL - boss_w, y, boss_w, boss_l))
else:
    assert boss <= 1e-9, "discs this thick would stand proud: use the bar layout's pads"
    inset = SHELL_WALL + 1.0 + MAG_D / 2
    top_y = CASE_H - SHELL_WALL - (CORNER_R - SHELL_WALL) - 1.0 - MAG_D / 2
    low_y = panel_y + 1.0 + MAG_D / 2
    for cy in (low_y, (low_y + top_y) / 2, top_y):
        DISCS += [(inset, cy), (CASE_W - inset, cy)]
parts = {"battery": (batt_x, batt_y, BATT_W, BATT_H), "adapter": (adapter_x, adapter_y, ADAPTER_W, ADAPTER_H),
         "xiao": (xiao_x, xiao_y, XIAO_W, XIAO_H)}


def clashes(bx, by, bw, bh):
    m = MAGNET_CLEAR
    return [n for n, (x, y, w, h) in parts.items() if bx + bw + m > x and bx - m < x + w and by + bh + m > y and by - m < y + h]


for b in BOSSES:
    assert not clashes(*b), (b, clashes(*b))
assert inner_depth - PANEL_T - CLEAR >= boss, "no room behind the panel for a magnet boss"
min_gap_to_battery = batt_x - (SHELL_WALL + boss_w)

fig, (ax, sx) = plt.subplots(1, 2, figsize=(13, 11), gridspec_kw={"width_ratios": [3, 1.1]})
INK, MUTED = "#15171A", "#5C636E"


def box(a, x, y, w, h, label=None, color=INK, ls="-", fill=None, alpha=1.0, fs=8, lw=1.2):
    a.add_patch(Rectangle((x, y), w, h, fill=fill is not None, facecolor=fill, edgecolor=color,
                          linestyle=ls, lw=lw, alpha=alpha))
    if label:
        a.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, color=color)


# Front view
box(ax, 0, 0, CASE_W, CASE_H, fill="#FFFFFF", lw=2)
box(ax, *win, fill="#DCE6F2")
ax.text(win[0] + win[2] / 2, win[1] + win[3] - 6, f"window {win[2]:.1f} x {win[3]:.1f}\n(active area {AA_W} x {AA_H}\nper drawing, minus {MASK} mask)",
        ha="center", va="top", fontsize=8, color=INK)
box(ax, panel_x, panel_y, PANEL_W, PANEL_H, color=MUTED, ls="--")
ax.text(panel_x + 1, panel_y + PANEL_H - 1.2, f"panel {PANEL_W} x {PANEL_H}", fontsize=7, color=MUTED, va="top")
box(ax, batt_x, batt_y, BATT_W, BATT_H, f"battery behind panel\n{BATT_W:g} x {BATT_H:g} x {BATT_T:g}", color="#B3261E", ls="--")
box(ax, adapter_x, adapter_y, ADAPTER_W, ADAPTER_H, f"adapter\nbehind\npanel\n{ADAPTER_W:.1f} x\n{ADAPTER_H:.1f}", color="#2457C5", ls="--", fs=7)
fpc_x = panel_x + (PANEL_W - FPC_EXIT_W) / 2
box(ax, fpc_x, panel_y - FOLD, FPC_EXIT_W, FOLD, color="#B26B00", ls=":", fill="#F6E3B4", alpha=0.6)
ax.text(fpc_x + FPC_EXIT_W / 2, panel_y - FOLD - 0.6, "FPC folds back here", ha="center", va="top", fontsize=7, color="#B26B00")
box(ax, xiao_x, xiao_y, XIAO_W, XIAO_H, "XIAO\nESP32-S3", color="#2F8A4E", fs=8)
ax.add_patch(Rectangle((xiao_x + XIAO_W, xiao_y + (XIAO_H - USB_W) / 2), USB_OVERHANG, USB_W, color="#2F8A4E", alpha=0.6))
ax.add_patch(FancyArrowPatch((CASE_W + 0.5, xiao_y + XIAO_H / 2), (CASE_W + 7, xiao_y + XIAO_H / 2), arrowstyle="-|>", mutation_scale=12, color="#2F8A4E"))
ax.text(CASE_W + 7.5, xiao_y + XIAO_H / 2, "USB-C", va="center", fontsize=8, color="#2F8A4E")
ax.plot([xiao_x + 1.5, 8], [xiao_y + 2.5, 3.2], color="#7B3FA0", lw=2.2)
ax.text(8, 4.6, "antenna (size TBD): along the chin, front side", fontsize=7, color="#7B3FA0")
# XIAO buttons face the back (board upside down). Which of the two is R (reset) is not known
# from the model (they mirror each other): check the real board. The pinhole is drawn over the lower one.
btn_x = xiao_x + XIAO_W - BTN_FROM_END
btn_ys = (xiao_y + BTN_FROM_SIDE, xiao_y + XIAO_H - BTN_FROM_SIDE)
for by in btn_ys:
    box(ax, btn_x - BTN_W / 2, by - BTN_H / 2, BTN_W, BTN_H, color="#2F8A4E", fill="#BFE3C9")
pin_x, pin_y = btn_x, btn_ys[0]
ax.add_patch(Circle((pin_x, pin_y), PINHOLE_D / 2, color=INK))
ax.annotate("rear pinhole over a XIAO button\n(R or B: check the real board)", (pin_x, pin_y), (24, 9.5), fontsize=7,
            color=INK, ha="center", arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
for bx, by, bw, bh in BOSSES:
    left = bx < CASE_W / 2
    mx = bx + (0 if left else BOSS_WALL) + MAG_GAP / 2
    ax.add_patch(Rectangle((mx, by + BOSS_WALL + MAG_GAP / 2), MAG_W, MAG_L, fill=False, ls=":", color=MUTED, lw=1.3))
for cx, cy in DISCS:
    ax.add_patch(Circle((cx, cy), MAG_D / 2, fill=False, ls=":", color=MUTED, lw=1.3))
mag_label = "12 x 8x3x1 bars\nin back pockets" if MAG_STYLE == "bars" else "6 x 8x0.6 discs,\nflush pockets"
ax.text(SHELL_WALL + 0.5, mag_bottom - 1.0, mag_label, fontsize=6, color=MUTED, va="top")
ax.annotate("", (0, -6), (CASE_W, -6), arrowprops=dict(arrowstyle="<->", color=INK))
ax.text(CASE_W / 2, -7, f"{CASE_W:.1f}", ha="center", va="top", fontsize=9)
ax.annotate("", (-6, 0), (-6, CASE_H), arrowprops=dict(arrowstyle="<->", color=INK))
ax.text(-7, CASE_H / 2, f"{CASE_H:.1f}", ha="right", va="center", fontsize=9, rotation=90)
ax.annotate("", (CASE_W + 3, 0), (CASE_W + 3, CHIN_H), arrowprops=dict(arrowstyle="<->", color=MUTED))
ax.text(CASE_W + 4, CHIN_H - 3, f"chin\n{CHIN_H:.1f}", fontsize=8, color=MUTED)
ax.set_title("Front view (parts behind the panel dashed)", fontsize=11)
ax.set_xlim(-14, CASE_W + 20); ax.set_ylim(-12, CASE_H + 6); ax.set_aspect("equal"); ax.axis("off")

# Side section through the middle (front on the left)
box(sx, 0, 0, CASE_T, CASE_H, fill="#FFFFFF", lw=2)
box(sx, FRONT_WALL, panel_y, PANEL_T, PANEL_H, color=MUTED, fill="#DCE6F2")
behind = FRONT_WALL + PANEL_T + CLEAR
box(sx, behind, batt_y, BATT_T, BATT_H, color="#B3261E", fill="#F6D6D3")
box(sx, behind, adapter_y, ADAPTER_T, ADAPTER_H, color="#2457C5", fill="#DCE4F6")
xz = FRONT_WALL + CLEAR                     # front of the joints
box(sx, xz, xiao_y + 4, JOINT, 4, color="#B26B00", fill="#F6E3B4")        # wire joints
box(sx, xz + JOINT, xiao_y, XIAO_BODY_T, XIAO_H, color="#2F8A4E", fill="#D6EEDD")
usb_y = xiao_y + (XIAO_H - USB_W) / 2
usb_top = xz + JOINT + XIAO_T
box(sx, xz + JOINT, usb_y, XIAO_T, USB_W, color="#2F8A4E", fill="#9FD3AF")
box(sx, CASE_T - BACK_WALL, usb_y - 0.3, BACK_WALL + 0.02, USB_W + 0.6, color="#FFFFFF", fill="#FFFFFF", lw=0)  # notch
sx.text(CASE_T + 1.5, usb_y + USB_W / 2, f"USB-C in a\nback notch\n({usb_top - CASE_T:+.1f} vs\nback face)", fontsize=7, color="#2F8A4E", va="center")
sx.plot([FRONT_WALL + PANEL_T / 2, FRONT_WALL + PANEL_T / 2, behind + 0.2, behind + 0.2],
        [panel_y, panel_y - FOLD + 0.5, panel_y - FOLD + 0.5, fpc_top_behind], color="#B26B00", lw=1.5)
for _, y, _, bh in BOSSES[::2]:   # the section is drawn through one side's column of bars
    box(sx, CASE_T - BACK_WALL - boss, y, boss, bh, color=MUTED, fill="#EEF0F2")
    box(sx, CASE_T - MAGNET_SKIN - MAGNET_T, y + BOSS_WALL + MAG_GAP / 2, MAGNET_T, MAG_L, color=MUTED, fill="#9AA0A8")
for _, cy in DISCS[::2]:
    box(sx, CASE_T - MAGNET_SKIN - MAGNET_T, cy - MAG_D / 2, MAGNET_T, MAG_D, color=MUTED, fill="#9AA0A8")
sx.annotate("", (0, -6), (CASE_T, -6), arrowprops=dict(arrowstyle="<->", color=INK))
sx.text(CASE_T / 2, -7, f"{CASE_T:.1f}", ha="center", va="top", fontsize=9)
sx.text(CASE_T + 1.5, panel_y + 40, "front\nwall\n|\npanel\n|\nbattery /\nadapter\n|\nback\nwall", fontsize=7, color=MUTED, va="center")
sx.set_title("Side section", fontsize=11)
sx.set_xlim(-4, CASE_T + 12); sx.set_ylim(-12, CASE_H + 6); sx.set_aspect("equal"); sx.axis("off")

fig.suptitle(f"Magnet layout v1 ({MAG_STYLE}): about {CASE_W:.1f} x {CASE_H:.1f} x {CASE_T:.1f} mm (datasheet numbers, unmeasured)", fontsize=13)
fig.tight_layout()
out = Path(__file__).with_name("layout_v1.png" if MAG_STYLE == "bars" else "layout_v1_discs.png")
fig.savefig(out, dpi=110)
print(f"case {CASE_W:.1f} x {CASE_H:.1f} x {CASE_T:.1f}; chin {CHIN_H:.1f}; inner depth {inner_depth:.1f}")
print(f"{MAG_STYLE}: {len(DISCS)} discs at {[(round(x, 1), round(y, 1)) for x, y in DISCS]}" if DISCS else f"{len(BOSSES)} magnet bars, pitch {pitch:.1f}, rows y {mag_bottom:.1f}..{mag_top:.1f}; boss {boss:.1f} into the cavity; gap boss-to-battery {min_gap_to_battery:.1f}")
pin_travel = CASE_T - (FRONT_WALL + CLEAR + JOINT + PCB_T + BTN_TOP)
print(f"pinhole at x {pin_x:.1f}, y {pin_y:.1f} (or y {btn_ys[1]:.1f}); pin travels {pin_travel:.1f} from the back face to the button")
print(f"usb-c top {usb_top:.2f} vs back face {CASE_T:.2f}: {usb_top - CASE_T:+.2f} (negative = inside)")
print(f"xiao x {xiao_x:.1f}..{xiao_x + XIAO_W:.1f} (inner wall at {CASE_W - CHIN_WALL:.1f}); usb face at {xiao_x + XIAO_W + USB_OVERHANG:.1f}")
print(f"adapter y {adapter_y:.1f}..{adapter_y + ADAPTER_H:.1f}; battery y {batt_y:.1f}..{batt_y + BATT_H:.1f}; panel top {panel_y + PANEL_H:.1f}; case top {CASE_H:.1f}")
print(f"wrote {out}")
