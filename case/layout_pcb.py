"""Phase 2 mockup (Erik: option B): custom PCB, module in a chin below the panel, 1 mm battery,
magnetic pogo pads instead of USB-C. Same 3:4 picture and masking as the compact case.
Mockup only: datasheet numbers, nothing measured, parts not chosen. See docs/phase2-custom-pcb.md.

    python3 case/layout_pcb.py     -> case/layout_pcb.png

The board straddles the panel's bottom edge: its lower part (in the chin, full case depth) carries
the ESP32-C6-MINI-1U module and the tall power parts; its upper part (behind the panel, thin
zone) carries only the panel connector and small capacitors. The panel cable folds 180 degrees
around the panel's bottom edge and runs up behind the panel into that connector, as today.
Units mm; x right, y up from the case's bottom edge (front view); z from the front face.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

# Parts (datasheets; unmeasured)
PANEL_W, PANEL_H, PANEL_T = 58.0, 85.64, 1.0
AA_W, AA_H, AA_LEFT, AA_TOP = 51.6, 77.04, 3.2, 2.55
FPC_EXIT_W, FPC_TAIL_W, FPC_LEN = 20.256, 26.0, 20.0
BATT_W, BATT_H, BATT_T = 44.0, 61.0, 1.0          # PowerStream PGEB016144, 200 mAh
MOD_W, MOD_L, MOD_T = 13.2, 12.5, 2.4              # ESP32-C6-MINI-1U (antenna socket)
PCB_T = 0.6                                         # board thickness (choice)
THIN_PARTS_T = 1.4                                  # tallest part allowed behind the panel
CONN_W, CONN_H = 30.0, 4.0                          # 32-pin 0.8 mm FPC connector, not chosen
ANT_W, ANT_H = 15.0, 10.0                           # flat antenna placeholder, size TBD
POGO_N, POGO_PITCH, POGO_D = 4, 2.5, 1.6            # pads; pins live on the charging cable
ALIGN_D = 3.0                                       # alignment magnets beside the pads
# Choices carried over from the compact case
WALL_SIDE, TOP_FRAME, CLEAR, SHELL_WALL, CHIN_WALL = 3.0, 3.0, 0.3, 1.2, 1.2
FRONT_WALL, BACK_WALL, FOLD, MASK = 1.0, 1.0, 2.0, 0.5
PIC_RATIO = 4 / 3
MAG_W, MAG_L, MAG_GAP, BOSS_WALL = 3.0, 8.0, 0.2, 1.0
CORNER_R = 4.0
MOD_MARGIN = 0.5                                    # board edge to module

CASE_W = PANEL_W + 2 * (WALL_SIDE + CLEAR)
board_y0 = CHIN_WALL + CLEAR
mod = (CASE_W - SHELL_WALL - CLEAR - MOD_MARGIN - MOD_W, board_y0 + MOD_MARGIN, MOD_W, MOD_L)
panel_y = mod[1] + MOD_L + CLEAR                    # panel sits just above the module
panel_x = WALL_SIDE + CLEAR
CASE_H = panel_y + PANEL_H + CLEAR + TOP_FRAME

# Depth: chin = board + module; behind the panel = panel + thin parts + board.
inner_chin = CLEAR + MOD_T + PCB_T
inner_panel = PANEL_T + CLEAR + THIN_PARTS_T + PCB_T
inner_batt = PANEL_T + CLEAR + BATT_T + CLEAR
INNER = max(inner_chin, inner_panel, inner_batt)
T = FRONT_WALL + INNER + BACK_WALL
max_batt_t = INNER - PANEL_T - CLEAR - CLEAR

# Picture window (as in the compact case)
aa_x = panel_x + AA_LEFT
win_w = AA_W - 2 * MASK
win_top = panel_y + PANEL_H - AA_TOP - MASK
win_h = win_w * PIC_RATIO
win = (aa_x + MASK, win_top - win_h, win_w, win_h)
masked = (aa_x, panel_y + PANEL_H - AA_TOP - AA_H, AA_W, win[1] - (panel_y + PANEL_H - AA_TOP - AA_H))

# Panel cable: folds under the panel edge, runs up behind the panel to the connector.
fpc_x = panel_x + (PANEL_W - FPC_TAIL_W) / 2
fold = (panel_x + (PANEL_W - FPC_EXIT_W) / 2, panel_y - FOLD, FPC_EXIT_W, FOLD)
fpc_up = (fpc_x, panel_y, FPC_TAIL_W, FPC_LEN - FOLD)
conn = (CASE_W / 2 - CONN_W / 2, panel_y + FPC_LEN - FOLD - CONN_H + 1.0, CONN_W, CONN_H)
board_y1 = conn[1] + CONN_H + 0.5
inner_x0, inner_x1 = SHELL_WALL + CLEAR, CASE_W - SHELL_WALL - CLEAR
ant = (inner_x0 + 0.5, board_y0 + 0.8, ANT_W, ANT_H)
board_notch = (inner_x0, board_y0, ANT_W + 1.5, panel_y - board_y0)   # no copper under the antenna
batt = (panel_x + (PANEL_W - BATT_W) / 2, board_y1 + CLEAR + 0.5, BATT_W, BATT_H)
inner_top = CASE_H - SHELL_WALL

# Chin parts beside the module (tall power parts: inductor, diodes, MOSFET, charger, LDO).
# Front side of the chin board, under the cable fold (the pogo pads are on the back side).
power = (board_notch[0] + board_notch[2] + 0.5, board_y0 + MOD_MARGIN,
         mod[0] - 1.0 - (board_notch[0] + board_notch[2] + 0.5), fold[1] - 0.5 - (board_y0 + MOD_MARGIN))
pogo_x0 = CASE_W / 2 - (POGO_N - 1) * POGO_PITCH / 2
pogo_y = board_y0 + 5.0
pads = [(pogo_x0 + i * POGO_PITCH, pogo_y) for i in range(POGO_N)]
aligns = [(pads[0][0] - 4.5, pogo_y), (pads[-1][0] + 4.5, pogo_y)]
button = (mod[0] - 2.5, board_y0 + 2.5)


def overlap(a, b, m=0.0):
    return a[0] < b[0] + b[2] + m and b[0] < a[0] + a[2] + m and a[1] < b[1] + b[3] + m and b[1] < a[1] + a[3] + m


# Checks
assert batt[1] + BATT_H <= inner_top - CLEAR, "battery hits the top wall"
assert not overlap(mod, fold, 0.5), "module hits the cable fold"
assert not overlap(mod, (panel_x, panel_y, PANEL_W, PANEL_H)), "module under the panel"
assert not overlap(ant, mod, 1.0) and not overlap(ant, fold, 1.0), "antenna crowds the module or cable"
assert power[2] > 3.0, "no room for the power parts"
assert conn[1] >= panel_y, "connector must be behind the panel"
assert BATT_T <= max_batt_t + 1e-9
boss_w, boss_l = MAG_W + MAG_GAP + BOSS_WALL, MAG_L + MAG_GAP + 2 * BOSS_WALL
top_y = CASE_H - CORNER_R - 1.0
bars = []
for side in ("L", "R"):
    start, n = board_y1 + 1.0, 6
    pitch = (top_y - start - boss_l) / (n - 1)
    x = SHELL_WALL if side == "L" else CASE_W - SHELL_WALL - boss_w
    bars += [(x, start + i * pitch, boss_w, boss_l) for i in range(n)]
for b in bars:
    assert not overlap(b, batt, 0.5), "magnet pad hits the battery"

# Drawing
INK, MUTED = "#15171A", "#5C636E"
RED, BLUE, GREEN, ORANGE, PURPLE = "#B3261E", "#2457C5", "#2F8A4E", "#B26B00", "#7B3FA0"
fig, axs = plt.subplots(1, 3, figsize=(17, 11), gridspec_kw={"width_ratios": [3, 1.1, 3]})


def box(a, r, label=None, color=INK, ls="-", fill=None, fs=7, lw=1.1, alpha=1.0, hatch=None):
    a.add_patch(Rectangle((r[0], r[1]), r[2], r[3], fill=fill is not None or hatch is not None, facecolor=fill or "none",
                          edgecolor=color, linestyle=ls, lw=lw, alpha=alpha, hatch=hatch))
    if label:
        a.text(r[0] + r[2] / 2, r[1] + r[3] / 2, label, ha="center", va="center", fontsize=fs, color=color)


def outline(a):
    a.add_patch(FancyBboxPatch((0, 0), CASE_W, CASE_H, boxstyle=f"round,pad=0,rounding_size={CORNER_R}",
                               fc="#FBFAF7", ec=INK, lw=2))


def dims(a, h_label=True):
    a.annotate("", (0, -6), (CASE_W, -6), arrowprops=dict(arrowstyle="<->", color=INK))
    a.text(CASE_W / 2, -7, f"{CASE_W:.1f}", ha="center", va="top", fontsize=10)
    if h_label:
        a.annotate("", (-5, 0), (-5, CASE_H), arrowprops=dict(arrowstyle="<->", color=INK))
        a.text(-6, CASE_H / 2, f"{CASE_H:.1f}", rotation=90, ha="right", va="center", fontsize=10)
    a.set_xlim(-12, CASE_W + 4); a.set_ylim(-12, CASE_H + 4); a.set_aspect("equal"); a.axis("off")


# Front view, parts behind dashed
ax = axs[0]
outline(ax)
box(ax, win, None, fill="#5E8C9A")
ax.add_patch(Rectangle((win[0], win[1]), win[2], win[3] * 0.35, fc="#6E8C5A", ec="none"))
ax.text(win[0] + win[2] / 2, win[1] + win[3] - 4, f"picture {win_w:.1f} x {win_h:.1f} (3:4)", ha="center", va="top",
        fontsize=9, color="white")
box(ax, masked, f"masked panel strip ({masked[3]:.1f})", color=MUTED, hatch="////", fs=7, alpha=0.6)
box(ax, (panel_x, panel_y, PANEL_W, PANEL_H), color=MUTED, ls="--")
board = [(inner_x0 + board_notch[2], board_y0, inner_x1 - inner_x0 - board_notch[2], panel_y - board_y0),
         (inner_x0, panel_y, inner_x1 - inner_x0, board_y1 - panel_y)]
for r in board:
    box(ax, r, None, color=GREEN, ls="--", fill="#E3F2E7", alpha=0.55)
ax.text(inner_x0 + 1, panel_y + 1.0, "board: thin parts\nbehind the panel", ha="left", va="bottom", fontsize=6.5, color=GREEN)
box(ax, batt, f"battery {BATT_W:g} x {BATT_H:g} x {BATT_T:g}\n(PGEB016144, 200 mAh)", color=RED, ls="--")
box(ax, fpc_up, None, color=ORANGE, ls=":", fill="#F6E3B4", alpha=0.5)
box(ax, fold, None, color=ORANGE, ls=":", fill="#F6E3B4", alpha=0.7)
ax.text(fpc_up[0] + fpc_up[2] / 2, panel_y + 6, "panel cable\n(folded behind)", ha="center", fontsize=6, color=ORANGE)
box(ax, conn, "32-pin connector", color=BLUE, ls="--", fs=6)
box(ax, mod, "ESP32-C6\nMINI-1U", color=GREEN, fill="#BFE3C9", fs=7)
box(ax, power, None, color=GREEN, ls="--")
ax.text(power[0] + 1, power[1] + power[3] - 1, "panel boost, charger, LDO, load switch,\naccelerometer (front side)",
        ha="left", va="top", fontsize=5.5, color=GREEN)
box(ax, ant, "antenna\n(size TBD)", color=PURPLE, fill="#EADCF3", fs=6.5)
ax.plot([ant[0] + ant[2], mod[0] + 2], [ant[1] + 1, mod[1] + 1], color=PURPLE, lw=0.9, ls="--")
for p in pads:
    ax.add_patch(Circle(p, POGO_D / 2, fc="none", ec=ORANGE, ls="--"))
ax.add_patch(Circle(button, 0.9, fc="#BFE3C9", ec=GREEN))
ax.annotate("setup button (front pinhole)", button, (button[0] - 14, -2.5), fontsize=6.5, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.7))
for b in bars:
    left = b[0] < CASE_W / 2
    box(ax, (b[0] + (0 if left else BOSS_WALL) + MAG_GAP / 2, b[1] + BOSS_WALL + MAG_GAP / 2, MAG_W, MAG_L), color=MUTED, ls=":")
dims(ax)
ax.set_title("Front view (parts behind dashed)", fontsize=11)

# Section through the middle (x = centre): front on the left
a = axs[1]
a.add_patch(Rectangle((0, 0), T, CASE_H, fc="#FFFFFF", ec=INK, lw=2))
zb = T - BACK_WALL - PCB_T                                    # board's front face
box(a, (FRONT_WALL, panel_y, PANEL_T, PANEL_H), color=MUTED, fill="#DCE6F2")
box(a, (zb, board_y0, PCB_T, board_y1 - board_y0), color=GREEN, fill="#BFE3C9")
box(a, (zb - 1.2, conn[1], 1.2, CONN_H), color=BLUE, fill="#DCE4F6")
box(a, (FRONT_WALL + PANEL_T + CLEAR, batt[1], BATT_T, BATT_H), color=RED, fill="#F6D6D3")
box(a, (zb - MOD_T, mod[1], MOD_T, MOD_L), color=GREEN, ls="--")       # module, off-centre (projected)
a.text(zb - MOD_T - 0.2, mod[1] + MOD_L / 2, "module\n(projected)", ha="right", va="center", fontsize=6, color=GREEN)
zf = FRONT_WALL + PANEL_T + 0.15
a.plot([FRONT_WALL + PANEL_T / 2, FRONT_WALL + PANEL_T / 2, zf, zf, zb - 1.2],
       [panel_y, panel_y - FOLD + 0.4, panel_y - FOLD + 0.4, conn[1] + 2, conn[1] + 2], color=ORANGE, lw=1.4)
a.add_patch(Rectangle((T - BACK_WALL - 0.01, pogo_y - 2.5), BACK_WALL + 0.02, 5.0, fc="white", ec="none"))
a.text(T + 0.6, pogo_y, "pogo window\nin back wall", fontsize=6.5, color=ORANGE, va="center")
a.annotate("", (0, -6), (T, -6), arrowprops=dict(arrowstyle="<->", color=INK))
a.text(T / 2, -7, f"{T:.2f}", ha="center", va="top", fontsize=10)
a.set_xlim(-3, T + 6); a.set_ylim(-12, CASE_H + 4); a.set_aspect("equal"); a.axis("off")
a.set_title("Section, centre\n(front left)", fontsize=10)

# Back view (mirrored: viewer's left is the front view's right)
ax = axs[2]
outline(ax)


def mx(r):
    return (CASE_W - r[0] - r[2], r[1], r[2], r[3])


for b in bars:
    left = b[0] < CASE_W / 2
    box(ax, mx((b[0] + (0 if left else BOSS_WALL) + MAG_GAP / 2, b[1] + BOSS_WALL + MAG_GAP / 2, MAG_W, MAG_L)),
        color=INK, fill="#C9CDD3")
win_r = (pads[0][0] - POGO_D, pogo_y - 2.5, (POGO_N - 1) * POGO_PITCH + 2 * POGO_D, 5.0)
box(ax, mx(win_r), None, color=ORANGE, fill="#FFF3DC")
for p, lbl in zip(pads, ("VBUS", "D-", "D+", "GND")):
    x = CASE_W - p[0]
    ax.add_patch(Circle((x, p[1]), POGO_D / 2, fc="#D9A441", ec=ORANGE))
    ax.text(x, p[1] + 2.0, lbl, ha="center", fontsize=5, color=ORANGE)
for p in aligns:
    ax.add_patch(Circle((CASE_W - p[0], p[1]), ALIGN_D / 2, fc="#C9CDD3", ec=INK))
ax.text(CASE_W / 2, pogo_y + 5.5, "magnetic pogo pads (the spring pins are on the cable)\n+ 2 keyed alignment magnets",
        ha="center", fontsize=7, color=ORANGE)
ax.text(CASE_W / 2, CASE_H / 2, "flat back\n12 fridge magnets (8 x 3 x 1)\nin pockets, 0.4 skin", ha="center",
        va="center", fontsize=8, color=MUTED)
dims(ax, h_label=False)
ax.set_title("Back view (fridge side)", fontsize=11)

chin = win[1]
fig.suptitle(f"Custom-PCB mockup (option B): {CASE_W:.1f} x {CASE_H:.1f} x {T:.2f} mm  "
             f"(compact XIAO case today: 64.6 x 96.5 x 6.85)", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = Path(__file__).with_name("layout_pcb.png")
fig.savefig(out, dpi=110)

print(f"case {CASE_W:.1f} x {CASE_H:.2f} x {T:.2f}; inner depth {INNER:.2f} "
      f"(chin {inner_chin:.2f}, behind panel {inner_panel:.2f}, battery {inner_batt:.2f})")
print(f"picture {win_w:.1f} x {win_h:.1f}; chin (bottom edge to picture) {chin:.1f} = {chin / CASE_H:.0%}")
print(f"panel bottom at y {panel_y:.1f}; board y {board_y0:.1f}..{board_y1:.1f}; battery y {batt[1]:.1f}..{batt[1] + BATT_H:.1f} "
      f"(top wall {inner_top:.1f}); thickest battery that fits free: {max_batt_t:.2f}")
print(f"power-parts strip {power[2]:.1f} x {power[3]:.1f}; wrote {out}")
