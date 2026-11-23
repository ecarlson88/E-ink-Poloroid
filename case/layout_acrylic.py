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
ANT_L, ANT_H, ANT_T = 44.0, 4.5, 0.2    # Cdebyte TX2400-FPC-4405 (listing specs; check the datasheet), with its tape
# Choices
SHEET_T, MASK_T = 1.0, 0.1              # acrylic sheet; vinyl mask on its back (all but the window)
TAPE_T = 0.25                           # tape between the mask and the tray's rim, rib and ledge
RIM_W, SHEET_GAP, SHEET_LIP = 1.2, 0.15, 0.8  # rim the sheet rests on, fit gap, lip flush with the sheet (Erik)
WALL = RIM_W + SHEET_GAP + SHEET_LIP     # side and top walls
BACK_WALL, CLEAR, FOLD, MASK = 1.0, 0.3, 2.0, 0.5
CHIN_WALL = 1.0                         # bottom wall: 1.0 so the antenna clears the cable fold (ledger); the
                                        # lip runs along it too, and the chin ledge carries the sheet there
PIC_RATIO = 4 / 3
XIAO_GAP = 0.65                         # Ruling: 0.75 less the mask's 0.1; joint room stays 0.45
JOINT = 0.45                            # battery wire joints on the XIAO's pads (as compact)
JOINT_CLEAR = 0.2                       # joints to the panel's back (compact: 0.3; the mask took 0.1)
JOINT_FROM_END = (8.0, 10.1)            # BAT pads, from the XIAO's USB-C end (underside_pads.png)
JOINT_SPREAD = 1.5                      # solder and wire beyond the pads
BATT_GAP = 1.0                          # adapter to battery (compact: 1.5)
SW_X = 12.0                             # switch centre
LEDGE_T = 0.8                           # chin strip under the sheet (bonding area): a separate flat part,
STRIP_STEP = 0.4                        # resting on a step this deep in the bottom and left walls (no overhang)
MAG_D, MAG_T, MAG_SKIN, MAG_GAP = 8.0, 0.6, 0.4, 0.2   # Erik's discs (measured 0.6), flush in the back wall
RIB_T, RIB_GAP, CORNER_R = 1.2, 30.0, 0.8   # Erik: 0.8 outer corners; sheet, pocket and cavity square
PIN_D = 1.2

CASE_W = PANEL_W + 2 * (CLEAR + WALL)
panel_x = WALL + CLEAR
panel_y = max(USB_LEN + CLEAR, CHIN_WALL + FOLD + CLEAR)
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
switch = (SW_X - SW_W / 2, CHIN_WALL, SW_W, SW_D)
backstop = (SW_X - SW_W / 2 - 1.0, CHIN_WALL + SW_D, SW_W + 2.0, RIB_T)
ledge_top = panel_y - FOLD - CLEAR
ledge = (WALL - STRIP_STEP, CHIN_WALL - STRIP_STEP, notch[0] - (WALL - STRIP_STEP),
         ledge_top - (CHIN_WALL - STRIP_STEP))                       # chin strip, up to the USB-C notch
# Antenna (Erik: option A): stuck to the back of the ledge, left of the USB-C notch, against the bottom wall
ant = (WALL + CLEAR, CHIN_WALL, ANT_L, ANT_H)
z_bond = SHEET_T + MASK_T + TAPE_T                   # where the rim, rib and ledge stop
z_ant = z_bond + LEDGE_T                             # antenna's front face, on the back of the chin strip
joint_y0 = xiao_y0 + JOINT_FROM_END[0] - JOINT_SPREAD  # lowest point of the battery joints
rib = (WALL, panel_y - CLEAR - RIB_T, CASE_W / 2 - RIB_GAP / 2 - WALL, RIB_T)

# Magnet discs (Erik): six, flush with the inside of the back wall (BackWall = skin + disc), two per
# side: low (above the chin; on the right, above the XIAO), middle and top (below the corners)
assert abs(MAG_SKIN + MAG_T - BACK_WALL) < 1e-9, "disc pockets must be flush with the inside"
inset = WALL + 1.0 + MAG_D / 2
low_y, top_y = panel_y + 1.0 + MAG_D / 2, CASE_H - 9.0      # top row: where it sat with the old 4 mm corners
discs = [(x, y) for y in (low_y, (low_y + top_y) / 2, top_y) for x in (inset, CASE_W - inset)]
discs[1] = (CASE_W - inset, xiao_y1 + CLEAR + 1.0 + MAG_D / 2)
disc_boxes = [(x - MAG_D / 2, y - MAG_D / 2, MAG_D, MAG_D) for x, y in discs]


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
# The ledge and antenna pass over the XIAO's underside below its battery joints, where the
# board is flat (pads only, no parts): they need CLEAR to the board, and the joints sit above them.
ledge_room = z_pads - (z_ant + ANT_T)
assert ledge_room >= CLEAR - 1e-9, "antenna/ledge hits the XIAO's underside"
assert joint_y0 >= max(ledge_top, CHIN_WALL + ANT_H) + CLEAR, "battery joints come down to the ledge or antenna"
assert ledge_top <= panel_y - FOLD - CLEAR + 1e-9, "ledge reaches the cable fold"
assert z_bond + LEDGE_T <= z_back_in - SW_T - CLEAR, "ledge hits the switch"
for d in disc_boxes:   # flush pockets stand nothing proud inside, so only plan clearances matter
    for name, part in (("XIAO", xiao), ("switch backstop", backstop), ("antenna", ant)):
        assert not overlap(d, part, CLEAR), f"magnet disc under the {name}"
    assert d[0] >= WALL and d[0] + d[2] <= CASE_W - WALL and d[1] + d[3] <= inner_top, "disc outside the cavity"
assert batt[1] + BATT_H <= inner_top - CLEAR + 1e-9, "battery hits the top wall"
assert rib[0] + rib[2] <= fold[0] - CLEAR, "rib hits the cable fold"
assert SHEET_LIP + SHEET_GAP < CHIN_WALL, "sheet edge misses the bottom wall and ledge"
assert RIM_W >= 1.0, "too little rim for the tape at the sides and top"
assert ant[0] + ant[2] <= notch[0] - CLEAR + 1e-9, "antenna runs into the USB-C notch"
assert ant[1] + ant[3] <= fold[1] + 1e-9, "antenna overlaps the cable fold"
assert not overlap(ant, rib), "antenna hits the cross rib"
assert z_ant + ANT_T <= z_back_in - SW_T - CLEAR, "antenna hits the switch"
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
box(ax, ant, None, color=PURPLE, ls="--")
ax.text(ant[0] + 10, ant[1] + ant[3] / 2, f"antenna {ANT_L:g} x {ANT_H:g} on the back of the chin strip (separate part)", va="center", fontsize=6, color=PURPLE)
box(ax, switch, None, color=INK, fill="#C9CDD3")
box(ax, backstop, None, color=INK, fill="#8E949C")
ax.add_patch(Rectangle((SW_X - PLUNGER_W / 2, 0), PLUNGER_W, CHIN_WALL, fc="white", ec=INK))
ax.annotate("setup button (D5), pressed\nupward from the bottom edge", (SW_X, 0), (SW_X - 8, -8), fontsize=7, color=INK,
            arrowprops=dict(arrowstyle="-|>", color=INK))
box(ax, rib, None, color=INK, fill="#C9CDD3")
for x, y in discs:
    ax.add_patch(Circle((x, y), MAG_D / 2, fc="none", ec=MUTED, ls=":"))
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
box(a, (z_bond, ledge[1], LEDGE_T, ledge[3]), None, color=PURPLE, fill="#EADCF3")
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

sheet_in = SHEET_LIP + SHEET_GAP
ax.add_patch(Rectangle((sheet_in, sheet_in), CASE_W - 2 * sheet_in, CASE_H - 2 * sheet_in, fc="none", ec=BLUE, lw=0.8))
ax.text(CASE_W / 2, CASE_H - 0.3, f"acrylic edge, in a {SHEET_LIP:g} lip", ha="center", va="top", fontsize=6, color=BLUE)
chin = win[1]
fig.suptitle(f"Acrylic-front case, 3:4 picture, mounting A: {CASE_W:.1f} x {CASE_H:.1f} x {T:.2f} mm "
             f"(compact today: 64.6 x 96.5 x 6.85)", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = Path(__file__).with_name("layout_acrylic.png")
fig.savefig(out, dpi=110)

print(f"case {CASE_W:.1f} x {CASE_H:.2f} x {T:.2f}; inner depth {INNER:.2f}; picture {win_w:.1f} x {win_h:.1f}, "
      f"chin (bottom edge to picture) {chin:.1f} = {chin / CASE_H:.0%}, side border {win[0]:.1f}")
print(f"XIAO x {xiao_x0:.1f}..{xiao_x1:.1f}, y {xiao_y0:.1f}..{xiao_y1:.1f}; rear pinhole at ({pin[0]:.1f}, {pin[1]:.1f})")
print(f"switch centre x {SW_X:g}, body {SW_W:g} x {SW_D:g} x {SW_T:g}; chin strip {ledge[2]:.1f} x {ledge[3]:.1f} x {LEDGE_T:g}, "
      f"antenna to the XIAO underside {ledge_room:.2f}; joints from y {joint_y0:.1f}")
print(f"bond stack: rim at {T - z_bond:.2f} from the back, then mask {MASK_T:g} + tape {TAPE_T:g} + sheet {SHEET_T:g}")
print(f"battery top {batt[1] + BATT_H:.2f} vs inner top {inner_top:.2f}; discs at " + ", ".join(f"({x:.1f}, {y:.1f})" for x, y in discs))
print(f"antenna x {ant[0]:.1f}..{ant[0] + ant[2]:.1f} (notch at {notch[0]:.2f}), y {ant[1]:.1f}..{ant[1] + ant[3]:.1f} (cable fold from {fold[1]:.1f}), front face {z_ant:.1f} from the front, {T - z_ant - ANT_T:.2f} from the back face; lowest left disc {disc_boxes[0][1] - ant[1] - ant[3]:.1f} above it")
print(f"sheet {CASE_W - 2 * sheet_in:.2f} x {CASE_H - 2 * sheet_in:.2f} (square) in a {SHEET_LIP:g} lip, gap {SHEET_GAP:g}; side walls {WALL:.2f}")
print(f"wrote {out}")
