"""Writes magnet_case.json, a SolidCraft script that builds the case v0 as a parametric
design: every size is a named parameter (Parameters panel), derived sizes are
expressions of them, and sketches follow the parameters when they change.

Layout and numbers: case/layout.py and docs/case-dimensions.md (datasheets, unmeasured).

Build (from this folder, SolidCraft 0.22):
    python3 build_case.py                 # layout v1, magnet bars    -> magnet_case.json
    python3 build_case.py discs           # layout v1, 8 x 0.6 discs  -> magnet_case_discs.json
    python3 build_case.py square          # square picture, bars      -> magnet_case_square.json
    python3 build_case.py square discs    # square picture, discs     -> magnet_case_square_discs.json
    solidcraft-cli run magnet_case.json --save magnet_case.solidcraft --out magnet_case.step

Coordinates (mm): x to the right and y up as seen from the front, z from the back face
(on the fridge, z = 0) toward the front. Two bodies: BackShell (an open tray) and
FrontFrame (the front plate with the window and a locating lip).
"""
import json
import sys
from pathlib import Path

# "bars": 12 x 8x3x1 bars upright along the side walls, on raised pads.
# "discs": 6 x 8 mm discs, 0.6 thick (Erik's measured magnets), flush with the inside of the
#          back wall (BackWall = MagSkin + MagT), so they can sit anywhere, even behind the battery.
# "square" (Erik, mounting B): the bottom of the panel is masked to a square picture; the XIAO
#          stands upright behind the masked strip, flipped so its parts face the front, with its
#          USB-C out of the bottom edge (an opening in the bottom wall plus a pocket under the front
#          frame) and the pinhole through the front of the chin. The back has no openings.
#          See case/layout_square.py.
ARGS = set(sys.argv[1:])
assert ARGS <= {"discs", "square"}, ARGS
STYLE = "discs" if "discs" in ARGS else "bars"
SQUARE = "square" in ARGS
MAG_ROWS_R = 5 if SQUARE else 6  # right-side bars (the XIAO takes the lowest spot in the square layout)

# name, expression, comment. Plain values are measured or chosen; the rest are derived.
MAG_ROWS = 6  # magnet bars per side; changing it needs a rebuild from this script

PARAMS = [
    # Parts (datasheets; measure and update)
    ("PanelW", "58 mm", "panel outline width"),
    ("PanelH", "85.64 mm", "panel outline height"),
    ("PanelT", "1 mm", "panel thickness (datasheet 0.85-0.9)"),
    ("AAW", "51.6 mm", "active area width (drawing; the table says 50.4: measure)"),
    ("AAH", "77.04 mm", "active area height (drawing; the table says 75.6: measure)"),
    ("AALeft", "3.2 mm", "panel left edge to active area"),
    ("AATop", "2.55 mm", "panel top edge to active area"),
    ("FpcLen", "20 mm", "panel cable length beyond the panel edge"),
    ("AdapterW", "20.647 mm", "DESPI-E01 width"),
    ("AdapterH", "35.185 mm", "DESPI-E01 length"),
    ("AdapterT", "3 mm", "adapter thickness with the header removed (guess: measure)"),
    ("BattT", "3 mm", "303450 battery thickness"),
    ("XiaoW", "21 mm", "XIAO ESP32-S3 length"),
    ("XiaoH", "17.8 mm", "XIAO ESP32-S3 width"),
    ("XiaoBodyT", "2.8 mm", "XIAO height without the USB-C (Erik measured 2.8; STEP model said 3.25)"),
    ("XiaoT", "4.4 mm", "XIAO height to the top of the USB-C (Erik measured 4.4; STEP model said 4.46)"),
    ("UsbOver", "1.5 mm", "USB-C overhang past the XIAO edge"),
    ("UsbW", "8.9 mm", "USB-C receptacle width"),
    ("UsbLen", "7.3 mm", "USB-C receptacle length including the overhang"),
    ("BtnFromEnd", "1.6 mm", "XIAO button centre from the USB-C end of the board"),
    ("BtnFromSide", "3 mm", "XIAO button centre from a long edge"),
    ("MagW", "3 mm", "magnet bar width (Erik: 8 x 3 x 1 bars)"),
    ("MagL", "8 mm", "magnet bar length (upright, along the side)"),
    ("MagT", "1 mm", "magnet bar thickness"),
    # Case choices
    ("Clear", "0.3 mm", "gap around parts"),
    ("XiaoGap", "0.75 mm", "space between the front wall and the XIAO's underside: clearance plus battery wire joints (Erik)"),
    ("SideFrame", "3 mm", "frame width beside the panel"),
    ("TopFrame", "3 mm", "frame width above the panel"),
    ("Fold", "2 mm", "room under the panel for the cable fold"),
    ("ChinWall", "1.2 mm", "chin wall below the XIAO"),
    ("Wall", "1.2 mm", "back shell side wall"),
    ("FrontWall", "1 mm", "front frame thickness"),
    ("BackWall", "1 mm", "back wall thickness"),
    ("CornerR", "4 mm", "outer corner radius"),
    ("Mask", "0.5 mm", "frame overlap onto the active area, per side"),
    ("PinD", "1.2 mm", "pinhole for a paperclip"),
    ("MagSkin", "0.4 mm", "plastic between magnet and fridge"),
    ("MagGap", "0.2 mm", "magnet pocket oversize"),
    ("BossWall", "1 mm", "wall around a magnet pocket"),
    ("RibT", "1.2 mm", "cross rib thickness (under the panel's bottom edge)"),
    ("RibGap", "30 mm", "centre gap in the cross ribs for the panel cable and wires"),
    ("FrontR", "0.45 mm", "fillet on the front face's outer edge (SolidCraft 0.22 allows up to ~0.5 on this 1 mm frame)"),
    ("BackR", "0.8 mm", "fillet on the back face's outer edge"),
    ("SeamR", "0.3 mm", "fillet on both edges of the frame/shell seam (a small glue-hiding groove)"),
    ("WinChamfer", "0.6 mm", "45 degree chamfer around the window on the front face"),
    ("LipW", "0.8 mm", "front frame locating lip width"),
    ("LipH", "0.6 mm", "front frame locating lip height"),
    ("LipGap", "0.15 mm", "lip clearance to the shell wall"),
    # Derived
    ("CaseW", "PanelW + 2 * (SideFrame + Clear)", "overall width"),
    ("ChinH", "Fold + XiaoH + 2 * Clear + ChinWall", "chin height"),
    ("CaseH", "ChinH + PanelH + 2 * Clear + TopFrame", "overall height"),
    ("Joint", "XiaoGap - Clear", "room left for the battery wire joints on the XIAO's underside pads"),
    ("InnerD", "max(max(PanelT + max(BattT, AdapterT), Joint + XiaoBodyT) + 2 * Clear, Clear + Joint + XiaoT - BackWall)",
     "inside depth: the thickest stack, and deep enough that the USB-C (through the back notch) stays flush with the back face"),
    ("ShellH", "BackWall + InnerD", "back shell height; the front frame sits on it"),
    ("PanelX", "SideFrame + Clear", "panel left edge"),
    ("PanelY", "ChinH + Clear", "panel bottom edge"),
    ("WinX", "PanelX + AALeft + Mask", "window left"),
    ("WinY", "PanelY + PanelH - AATop - AAH + Mask", "window bottom"),
    ("WinW", "AAW - 2 * Mask", "window width"),
    ("WinH", "AAH - 2 * Mask", "window height"),
    ("XiaoX", "CaseW - UsbOver - XiaoW", "XIAO left edge (USB-C face flush with the right side)"),
    ("XiaoY", "ChinWall + Clear", "XIAO bottom edge"),
    ("UsbCY", "XiaoY + XiaoH / 2", "USB-C centre height"),
    ("RibY", "PanelY - Clear - RibT", "cross rib bottom edge"),
    ("PinX", "XiaoX + XiaoW - BtnFromEnd", "pinhole x (over a XIAO button)"),
    ("PinY", "XiaoY + BtnFromSide", "pinhole y (the lower button: check which is reset)"),
    ("AdapterY", "PanelY + FpcLen - Fold - 3 mm", "adapter bottom edge (folded cable end)"),
    ("BossW", "MagW + MagGap + BossWall", "magnet boss width from the side wall inward"),
    ("BossL", "MagL + MagGap + 2 * BossWall", "magnet boss length"),
    ("MagBottom", "PanelY + 1 mm", "bottom of the lowest magnet boss"),
    ("MagTop", "CaseH - CornerR - 1 mm", "top of the highest magnet boss (below the rounded corner)"),
    ("MagPitch", f"(MagTop - MagBottom - BossL) / {MAG_ROWS - 1}", "spacing between magnet rows"),
]

cmds = []


def c(command, **params):
    cmds.append({"command": command, "params": params})


def rounded_rect(x0, y0, x1, y1, r, first_line):
    """Closed outline with expression corners, its corners rounded with radius r.
    first_line: the id number the sketch will give its first line (l1, l5, ...)."""
    c("sketch.line", points=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]], closed=True)
    n = first_line
    c("sketch.fillet", points=[f"l{n}.start", f"l{n}.end", f"l{n + 1}.end", f"l{n + 2}.end"], radius=r)


def rect(x0, y0, x1, y1):
    c("sketch.line", points=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]], closed=True)


def set_param(name, expr, comment=None, after=None):
    """Replace a parameter's expression in place, or insert it after another one."""
    names = [n for n, _, _ in PARAMS]
    if name in names:
        i = names.index(name)
        PARAMS[i] = (name, expr, comment or PARAMS[i][2])
    else:
        PARAMS.insert(names.index(after) + 1 if after else len(PARAMS), (name, expr, comment or ""))


if SQUARE:
    # The panel sits just above the USB-C body; ChinH's slot becomes PanelY so later expressions see it.
    i = [n for n, _, _ in PARAMS].index("ChinH")
    PARAMS[i] = ("PanelY", "max(UsbLen + Clear, ChinWall + Fold + Clear)", "panel bottom edge: just above the USB-C body")
    PARAMS[:] = [p for j, p in enumerate(PARAMS) if not (p[0] == "PanelY" and j > i)]
    set_param("CaseH", "PanelY + PanelH + Clear + TopFrame", "overall height")
    set_param("InnerD", "max(PanelT + max(BattT, AdapterT) + 2 * Clear, PanelT + Clear + XiaoBodyT + XiaoGap)",
              "inside depth: the panel + battery stack, or the panel + the flipped XIAO behind it")
    set_param("XiaoGap", "0.75 mm", "space between the back wall and the flipped XIAO's underside: clearance plus battery wire joints (Erik)")
    set_param("WinY", "PanelY + PanelH - AATop - Mask - (AAW - 2 * Mask)", "window bottom (square picture at the top of the panel)")
    set_param("WinH", "WinW", "window height: square")
    set_param("XiaoX", "CaseW - Wall - Clear - XiaoH", "XIAO left edge (upright, at the right)")
    set_param("XiaoY", "UsbOver", "XIAO bottom edge (USB-C face flush with the bottom edge)")
    i = [n for n, _, _ in PARAMS].index("UsbCY")
    PARAMS[i] = ("UsbCX", "XiaoX + XiaoH / 2", "USB-C centre x")
    set_param("PinX", "XiaoX + BtnFromSide", "front pinhole x (over a XIAO button: check which one is reset)")
    set_param("PinY", "XiaoY + BtnFromEnd", "front pinhole y")
    PARAMS.append(("UsbPocket", "BackWall + XiaoGap + XiaoT + 0.1 mm - ShellH", "how far the USB-C pocket goes into the front frame"))
    if STYLE == "bars":
        PARAMS += [
            ("MagBottomR", "XiaoY + XiaoW + Clear + 0.5 mm", "bottom of the lowest right magnet boss (above the XIAO)"),
            ("MagPitchR", f"(MagTop - MagBottomR - BossL) / {MAG_ROWS_R - 1}", "spacing between right magnet rows"),
        ]

if STYLE == "discs":
    drop = {"MagW", "MagL", "BossW", "BossL", "MagBottom", "MagTop", "MagPitch", "BossWall", "BackWall"}
    PARAMS = [p for p in PARAMS if p[0] not in drop]
    i = [n for n, _, _ in PARAMS].index("MagT")
    PARAMS[i] = ("MagT", "0.6 mm", "magnet disc thickness (Erik measured 0.6)")
    PARAMS.insert(i, ("MagD", "8 mm", "magnet disc diameter"))
    i = [n for n, _, _ in PARAMS].index("MagGap") + 1
    PARAMS.insert(i, ("BackWall", "MagSkin + MagT", "back wall thickness: exactly skin + magnet, so the pockets are flush inside"))
    PARAMS += [
        ("DiscInset", "Wall + 1 mm + MagD / 2", "disc centre from the outer side"),
        ("DiscLowY", "PanelY + 1 mm + MagD / 2", "lower disc row (just above the chin)"),
        ("DiscTopY", "CaseH - CornerR - 1 mm - MagD / 2", "upper disc row (below the rounded corners)"),
        ("DiscMidY", "(DiscLowY + DiscTopY) / 2", "middle disc row"),
    ]
    if SQUARE:
        PARAMS.append(("DiscLowYR", "XiaoY + XiaoW + Clear + 1 mm + MagD / 2", "lower right disc (above the XIAO)"))

for name, expr, comment in PARAMS:
    c("parameters.add", name=name, expression=expr, comment=comment)

# Back shell: a rounded block, hollowed from the front down to the back wall.
c("sketch.create", plane="XY", name="ShellOutline")
rounded_rect(0, 0, "CaseW", "CaseH", "CornerR", 1)
c("sketch.finish")
c("solid.extrude", distance="ShellH", name="Shell", body_name="BackShell")

c("sketch.create", plane="XY", offset="ShellH", name="Cavity")
rounded_rect("Wall", "Wall", "CaseW - Wall", "CaseH - Wall", "CornerR - Wall", 1)
c("sketch.finish")
c("solid.extrude", distance="InnerD", direction="negative", operation="cut", targets=["BackShell"], name="Hollow")

if STYLE == "bars":
    # Magnet bars stand upright against each side wall: a boss on the inside of the back wall
    # (the side wall is its outer side) with a pocket open on the inside, leaving MagSkin.
    bosses, pockets = [], []
    for i in range(MAG_ROWS):
        y0 = f"MagBottom + {i} * MagPitch"
        # left side: the boss starts inside the side wall so it merges with it
        bosses.append(("Wall - 0.5 mm", y0, "Wall + BossW", f"{y0} + BossL"))
        pockets.append(("Wall", f"{y0} + BossWall", "Wall + MagW + MagGap", f"{y0} + BossWall + MagL + MagGap"))
    for i in range(MAG_ROWS_R):
        y0 = f"MagBottomR + {i} * MagPitchR" if SQUARE else f"MagBottom + {i} * MagPitch"
        # right side, mirrored
        bosses.append(("CaseW - Wall - BossW", y0, "CaseW - Wall + 0.5 mm", f"{y0} + BossL"))
        pockets.append(("CaseW - Wall - MagW - MagGap", f"{y0} + BossWall", "CaseW - Wall", f"{y0} + BossWall + MagL + MagGap"))

    c("sketch.create", plane="XY", offset="BackWall", name="MagnetBosses")
    for b in bosses:
        rect(*b)
    c("sketch.finish")
    c("solid.extrude", distance="MagSkin + MagT - BackWall", operation="join", targets=["BackShell"], name="Bosses")

    c("sketch.create", plane="XY", offset="MagSkin + MagT", name="MagnetPockets")
    for p in pockets:
        rect(*p)
    c("sketch.finish")
    c("solid.extrude", distance="MagT", direction="negative", operation="cut", targets=["BackShell"], name="Pockets")

else:
    # Flush disc pockets from the inside of the back wall, leaving MagSkin.
    discs = [(x, y) for y in ("DiscLowY", "DiscMidY", "DiscTopY") for x in ("DiscInset", "CaseW - DiscInset")]
    if SQUARE:
        discs[1] = ("CaseW - DiscInset", "DiscLowYR")
    c("sketch.create", plane="XY", offset="BackWall", name="MagnetPockets")
    for i, (dx, dy) in enumerate(discs, start=1):
        c("sketch.circle.center", center=[dx, dy], diameter=8)
        c("sketch.dimension", entities=[f"c{i}"], type="diameter", value="MagD + MagGap")
    c("sketch.finish")
    c("solid.extrude", distance="MagT", direction="negative", operation="cut", targets=["BackShell"], name="Pockets")

# Cross ribs: from the back wall up to the front frame, just below the panel's bottom edge,
# with a centre gap for the panel cable's fold and the wires. They support the frame across
# its middle (a second glue line), stop the panel's bottom edge and stiffen the shell.
c("sketch.create", plane="XY", offset="BackWall", name="CrossRibs")
# The ribs stop short of the side walls so the front frame's lip (just inside the walls) passes.
rect("Wall + 2 * LipGap + LipW", "RibY", "CaseW / 2 - RibGap / 2", "RibY + RibT")
if not SQUARE:   # in the square layout the XIAO takes the right rib's place
    rect("CaseW / 2 + RibGap / 2", "RibY", "CaseW - Wall - 2 * LipGap - LipW", "RibY + RibT")
c("sketch.finish")
c("solid.extrude", distance="InnerD", operation="join", targets=["BackShell"], name="Ribs")

if not SQUARE:
    # Pinhole through the back wall, over one of the XIAO's buttons.
    c("sketch.create", plane="XY", name="Pinhole")
    c("sketch.circle.center", center=["PinX", "PinY"], diameter=1.2)
    c("sketch.dimension", entities=["c1"], type="diameter", value="PinD")
    c("sketch.finish")
    c("solid.extrude", distance="BackWall", operation="cut", targets=["BackShell"], name="PinholeCut")

    # USB-C: the receptacle sits in a notch through the back wall and the side wall, its face
    # flush with the outside, so a cable's plug (whose grip stays outside the case) seats fully.
    c("sketch.create", plane="XY", name="UsbNotch")
    rect("XiaoX + XiaoW - (UsbLen - UsbOver) - Clear", "UsbCY - UsbW / 2 - Clear", "CaseW + 1 mm", "UsbCY + UsbW / 2 + Clear")
    c("sketch.finish")
    c("solid.extrude", distance="ShellH", operation="cut", targets=["BackShell"], name="UsbNotchCut")

else:
    # USB-C out of the bottom edge: an opening in the bottom wall above the flipped board's
    # underside (the back stays closed), and a pocket under the front frame further down.
    c("sketch.create", plane="XY", offset="BackWall + XiaoGap - Clear", name="UsbOpening")
    rect("UsbCX - UsbW / 2 - Clear", "-1 mm", "UsbCX + UsbW / 2 + Clear", "ChinWall + 0.5 mm")
    c("sketch.finish")
    c("solid.extrude", distance="ShellH", operation="cut", targets=["BackShell"], name="UsbOpeningCut")

# Front frame: a plate on the shell with the window cut through it.
c("sketch.create", plane="XY", offset="ShellH", name="FrameOutline")
rounded_rect(0, 0, "CaseW", "CaseH", "CornerR", 1)
c("sketch.finish")
c("solid.extrude", distance="FrontWall", operation="new", name="Frame", body_name="FrontFrame")

c("sketch.create", plane="XY", offset="ShellH + FrontWall", name="Window")
rect("WinX", "WinY", "WinX + WinW", "WinY + WinH")
c("sketch.finish")
c("solid.extrude", distance="FrontWall", direction="negative", operation="cut", targets=["FrontFrame"], name="WindowCut")

# Locating lip under the frame, just inside the shell walls.
c("sketch.create", plane="XY", offset="ShellH", name="Lip")
rounded_rect("Wall + LipGap", "Wall + LipGap", "CaseW - Wall - LipGap", "CaseH - Wall - LipGap", "CornerR - Wall - LipGap", 1)
rounded_rect("Wall + LipGap + LipW", "Wall + LipGap + LipW", "CaseW - Wall - LipGap - LipW", "CaseH - Wall - LipGap - LipW",
             "CornerR - Wall - LipGap - LipW", 5)
c("sketch.finish")
c("solid.extrude", distance="LipH", direction="negative", operation="join", targets=["FrontFrame"], name="LipRing")

if SQUARE:
    # USB-C pocket under the front frame (also notching the lip there), and the front pinhole.
    c("sketch.create", plane="XY", offset="ShellH - LipH - 0.1 mm", name="UsbPocket")
    rect("UsbCX - UsbW / 2 - Clear", "-1 mm", "UsbCX + UsbW / 2 + Clear", "UsbLen + Clear")
    c("sketch.finish")
    c("solid.extrude", distance="LipH + 0.1 mm + UsbPocket", operation="cut", targets=["FrontFrame"], name="UsbPocketCut")
    c("sketch.create", plane="XY", offset="ShellH + FrontWall", name="Pinhole")
    c("sketch.circle.center", center=["PinX", "PinY"], diameter=1.2)
    c("sketch.dimension", entities=["c1"], type="diameter", value="PinD")
    c("sketch.finish")
    c("solid.extrude", distance="FrontWall", direction="negative", operation="cut", targets=["FrontFrame"], name="PinholeCut")

# --- Edge finishing ------------------------------------------------------------------------
# SolidCraft picks an edge by a point on it (plain numbers) and then keeps it by geometry, so
# these points come from the default parameter values and the fillets follow later changes.
# Each rounded outline is listed edge by edge: four straight edges and four corner arcs.
import math


def values():
    env = {"max": max, "min": min}
    for name, expr, _ in PARAMS:
        env[name] = eval(expr.replace(" mm", "").replace("mm", ""), {}, env)
    return env


v = values()
W, H, R = v["CaseW"], v["CaseH"], v["CornerR"]
k = R * (1 - 1 / math.sqrt(2))                     # 45 degree point on a corner arc
if SQUARE:
    notch_hi = v["UsbCX"] + v["UsbW"] / 2 + v["Clear"]
else:
    notch_lo = v["UsbCY"] - v["UsbW"] / 2 - v["Clear"]


def outline(z, right_split=False, bottom_split=False):
    pts = [[W / 2, 0, z], [W / 2, H, z], [0, H / 2, z],
           [k, k, z], [W - k, k, z], [W - k, H - k, z], [k, H - k, z]]
    if right_split:   # the USB-C notch splits the right edge in two
        pts += [[W, (R + notch_lo) / 2, z], [W, H / 2, z]]
    else:
        pts += [[W, H / 2, z]]
    if bottom_split:  # the bottom USB-C opening splits the bottom edge: add the piece to its right
        pts += [[(notch_hi + W - R) / 2, 0, z]]
    return pts


top = v["ShellH"] + v["FrontWall"]
c("solid.fillet", edges=outline(top), radius="FrontR", body="FrontFrame", name="FrontEdgeFillet")
c("solid.fillet", edges=outline(v["ShellH"], bottom_split=SQUARE), radius="SeamR", body="FrontFrame", name="FrameSeamFillet")
c("solid.fillet", edges=outline(v["ShellH"], right_split=not SQUARE, bottom_split=SQUARE), radius="SeamR", body="BackShell", name="ShellSeamFillet")
c("solid.fillet", edges=outline(0, right_split=not SQUARE), radius="BackR", body="BackShell", name="BackEdgeFillet")
wx, wy, ww, wh = v["WinX"], v["WinY"], v["WinW"], v["WinH"]
c("solid.chamfer", edges=[[wx + ww / 2, wy, top], [wx + ww / 2, wy + wh, top], [wx, wy + wh / 2, top], [wx + ww, wy + wh / 2, top]],
  distance="WinChamfer", body="FrontFrame", name="WindowChamfer")

c("inspect.measure")

out = Path(__file__).with_name("magnet_case" + ("_square" if SQUARE else "") + ("_discs" if STYLE == "discs" else "") + ".json")
out.write_text(json.dumps(cmds, indent=1) + "\n")
print(f"wrote {out} ({len(cmds)} commands, {len(PARAMS)} parameters)")
