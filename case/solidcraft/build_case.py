"""Writes magnet_case.json, a SolidCraft script that builds the case v0 as a parametric
design: every size is a named parameter (Parameters panel), derived sizes are
expressions of them, and sketches follow the parameters when they change.

Layout and numbers: case/layout.py and docs/case-dimensions.md (datasheets, unmeasured).

Build (from this folder, SolidCraft 0.22):
    python3 build_case.py                 # layout v1, magnet bars    -> magnet_case.json
    python3 build_case.py discs           # layout v1, 8 x 0.6 discs  -> magnet_case_discs.json
    python3 build_case.py compact         # compact case, 3:4 picture, bars  -> magnet_case_compact.json
    python3 build_case.py compact discs   # compact case, 3:4 picture, discs -> magnet_case_compact_discs.json
    python3 build_case.py acrylic         # acrylic-front case (discs only) -> magnet_case_acrylic.json (+ acrylic_sheet.svg)
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
# "compact" (Erik, mounting B): the XIAO stands upright behind the bottom of the panel, flipped
#          so its parts face the front, with its USB-C out of the bottom edge (an opening in the
#          bottom wall plus a pocket under the front frame) and the pinhole through the front of
#          the chin. The back has no openings. The picture is 3:4 (PicRatio): the frame masks the
#          bottom of the panel for a Polaroid-like chin. See case/layout_compact.py.
# "acrylic" (Erik): an additional case type on the compact layout: a 1 mm acrylic sheet (no holes,
#          so glass can replace it) with a vinyl mask on its back covers the whole front; one tray
#          holds everything. XIAO in mounting A (parts face the back, USB-C flush in a notch through
#          the back and bottom walls, rear reset pinhole); a side-actuated setup switch (D5) in the
#          chin, pressed from the bottom edge; a ledge under the sheet across the chin (tape area,
#          the slim antenna sticks to its back). See case/layout_acrylic.py and
#          docs/superpowers/specs/2026-11-22-acrylic-front-case-design.md.
ARGS = set(sys.argv[1:])
assert ARGS <= {"discs", "compact", "acrylic"}, ARGS
ACRYLIC = "acrylic" in ARGS
STYLE = "discs" if "discs" in ARGS or ACRYLIC else "bars"   # Erik: the acrylic case uses his 8 mm discs only
SQUARE = "compact" in ARGS or ACRYLIC   # the compact layout (named for its first, square-picture version)
MOUNT_B = SQUARE and not ACRYLIC         # the compact case's flipped XIAO, front pinhole and USB pocket
MAG_ROWS_R = 5 if SQUARE else 6  # right-side bars (above the XIAO in the compact layouts)

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
    set_param("PicRatio", "4 / 3", "picture height / width (Erik: 3:4; 1 = square, 1.5 = full screen)", after="Mask")
    set_param("WinY", "PanelY + PanelH - AATop - Mask - (AAW - 2 * Mask) * PicRatio", "window bottom (the picture sits at the top of the panel)")
    set_param("WinH", "WinW * PicRatio", "window height")
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

if ACRYLIC:
    drop = {"SideFrame", "TopFrame", "FrontWall", "FrontR", "SeamR", "WinChamfer", "LipW", "LipH", "LipGap", "UsbPocket"}
    PARAMS = [p for p in PARAMS if p[0] not in drop]
    set_param("SheetT", "1 mm", "front sheet: 1 mm acrylic (glass-ready: flat, no holes)", after="Clear")
    set_param("MaskT", "0.1 mm", "white vinyl mask on the back of the sheet (all of it but the window)", after="SheetT")
    set_param("TapeT", "0.25 mm", "tape between the mask and the tray's rim, rib and ledge (thin VHB; measure yours)", after="MaskT")
    set_param("RimR", "0.3 mm", "fillet on the lip's top outer edge", after="BackR")
    set_param("ChinWall", "1 mm", "bottom wall: 1.0 so the slim antenna clears the cable fold (ledger); the chin ledge carries the sheet there")
    set_param("RimW", "1.2 mm", "side and top rim the sheet rests on (through the mask and tape)", after="ChinWall")
    set_param("SheetGap", "0.15 mm", "fit gap round the sheet in its pocket, per side", after="RimW")
    set_param("SheetLip", "0.8 mm", "lip round the sheet, flush with its face (Erik); keep SheetLip + SheetGap below ChinWall, or the bottom lip runs past the bottom wall", after="SheetGap")
    set_param("Wall", "RimW + SheetGap + SheetLip", "side and top wall: rim + gap + lip")
    set_param("XiaoGap", "0.65 mm", "panel back to the XIAO's underside: 0.45 joints + 0.2 clearance (the mask took 0.1)")
    set_param("CaseW", "PanelW + 2 * (Clear + Wall)", "overall width (no frame: the mask covers the panel border)")
    set_param("CaseH", "PanelY + PanelH + Clear + Wall", "overall height")
    set_param("PanelX", "Wall + Clear", "panel left edge")
    set_param("InnerD", "max(max(MaskT + PanelT + max(BattT, AdapterT) + 2 * Clear, MaskT + PanelT + XiaoGap + XiaoBodyT + Clear), "
              "MaskT + PanelT + XiaoGap + XiaoT - BackWall)",
              "inside depth: panel + battery, panel + XIAO, or deep enough that the USB-C ends flush with the back face")
    set_param("PinX", "XiaoX + XiaoH - BtnFromSide", "rear pinhole x (mounting A mirrors the buttons: check which one is reset)")
    PARAMS += [
        ("SwX", "12 mm", "setup switch centre x (left of the XIAO)"),
        ("SwW", "3.5 mm", "setup switch body width (placeholder until the part is chosen)"),
        ("SwD", "2.9 mm", "setup switch body depth, from the bottom wall inward (placeholder)"),
        ("SwT", "1.6 mm", "setup switch body height, from the back wall (placeholder)"),
        ("PlungerW", "1.6 mm", "plunger slot width through the bottom wall (placeholder)"),
        ("PlungerH", "1 mm", "plunger slot height (placeholder)"),
        ("LedgeT", "0.8 mm", "chin strip thickness (a separate part under the sheet: tape area; the antenna sticks to its back)"),
        ("LedgeTop", "PanelY - Fold - Clear", "top edge of the chin strip (clear of the panel cable fold)"),
        ("StripStep", "0.4 mm", "step cut into the bottom and left walls that the chin strip rests on"),
        ("StripGap", "0.1 mm", "fit gap between the chin strip and its step"),
        ("StripEnd", "UsbCX - UsbW / 2 - Clear", "right end of the chin strip and its step (the USB-C notch)"),
        ("BondZ", "ShellH - MaskT - TapeT", "tray rim height: the mask and the tape lie on the rim, rib and ledge"),
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

UNITLESS = {"PicRatio"}   # SolidCraft reads a bare number as mm unless the unit is given as ""
for name, expr, comment in PARAMS:
    if name in UNITLESS:
        c("parameters.add", name=name, expression=expr, unit="", comment=comment)
    else:
        c("parameters.add", name=name, expression=expr, comment=comment)

# Back shell (the acrylic case's Tray): a rounded block, hollowed from the front down to the back wall.
SHELL = "Tray" if ACRYLIC else "BackShell"
c("sketch.create", plane="XY", name="ShellOutline")
rounded_rect(0, 0, "CaseW", "CaseH", "CornerR", 1)
c("sketch.finish")
c("solid.extrude", distance="ShellH + SheetT" if ACRYLIC else "ShellH", name="Shell", body_name=SHELL)
if ACRYLIC:
    # Pocket for the sheet: inset by the lip, down to the rim (BondZ) where the mask and tape sit.
    c("sketch.create", plane="XY", offset="ShellH + SheetT", name="SheetPocket")
    rounded_rect("SheetLip", "SheetLip", "CaseW - SheetLip", "CaseH - SheetLip", "CornerR - SheetLip", 1)
    c("sketch.finish")
    c("solid.extrude", distance="SheetT + MaskT + TapeT", direction="negative", operation="cut", targets=[SHELL],
      name="SheetPocketCut")

c("sketch.create", plane="XY", offset="BondZ" if ACRYLIC else "ShellH", name="Cavity")
rounded_rect("Wall", "ChinWall" if ACRYLIC else "Wall", "CaseW - Wall", "CaseH - Wall", "CornerR - Wall", 1)
c("sketch.finish")
c("solid.extrude", distance="InnerD - MaskT - TapeT" if ACRYLIC else "InnerD", direction="negative", operation="cut",
  targets=[SHELL], name="Hollow")

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
    c("solid.extrude", distance="MagSkin + MagT - BackWall", operation="join", targets=[SHELL], name="Bosses")

    c("sketch.create", plane="XY", offset="MagSkin + MagT", name="MagnetPockets")
    for p in pockets:
        rect(*p)
    c("sketch.finish")
    c("solid.extrude", distance="MagT", direction="negative", operation="cut", targets=[SHELL], name="Pockets")

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
    c("solid.extrude", distance="MagT", direction="negative", operation="cut", targets=[SHELL], name="Pockets")

# Cross ribs: from the back wall up to the front frame, just below the panel's bottom edge,
# with a centre gap for the panel cable's fold and the wires. They support the frame across
# its middle (a second glue line), stop the panel's bottom edge and stiffen the shell.
c("sketch.create", plane="XY", offset="BackWall", name="CrossRibs")
# The ribs stop short of the side walls so the front frame's lip (just inside the walls) passes.
if ACRYLIC:   # no lip: the rib runs into the wall and up to the sheet, which it also carries
    rect("Wall - 0.5 mm", "RibY", "CaseW / 2 - RibGap / 2", "RibY + RibT")
else:
    rect("Wall + 2 * LipGap + LipW", "RibY", "CaseW / 2 - RibGap / 2", "RibY + RibT")
if not SQUARE:   # in the square layout the XIAO takes the right rib's place
    rect("CaseW / 2 + RibGap / 2", "RibY", "CaseW - Wall - 2 * LipGap - LipW", "RibY + RibT")
c("sketch.finish")
c("solid.extrude", distance="InnerD - MaskT - TapeT" if ACRYLIC else "InnerD", operation="join", targets=[SHELL], name="Ribs")

if ACRYLIC:
    # Chin strip: a separate flat part (printed on the bed, so no overhang in the tray) under the
    # sheet across the chin: tape area, and the antenna sticks to its back. It rests on a step cut
    # into the bottom and left walls (the step faces up, so it prints); outer corner chamfered so
    # the step stays inside the case's rounded corner. Glue it to the step.
    def chin_outline(inset):
        x0, y0 = f"Wall - StripStep + {inset}", f"ChinWall - StripStep + {inset}"
        c("sketch.line", points=[[f"CornerR + {inset}", y0], ["StripEnd", y0], ["StripEnd", "LedgeTop"],
                                 [x0, "LedgeTop"], [x0, f"ChinWall + CornerR - Wall + {inset}"]], closed=True)

    c("sketch.create", plane="XY", offset="BondZ", name="ChinStep")
    chin_outline("0 mm")
    c("sketch.finish")
    c("solid.extrude", distance="LedgeT", direction="negative", operation="cut", targets=[SHELL], name="ChinStepCut")
    c("sketch.create", plane="XY", offset="BondZ - LedgeT", name="ChinStripOutline")
    chin_outline("StripGap")
    c("sketch.finish")
    c("solid.extrude", distance="LedgeT", operation="new", name="Strip", body_name="ChinStrip")

    # Setup switch: a backstop rib behind its body, and the plunger slot through the bottom wall.
    c("sketch.create", plane="XY", offset="BackWall", name="SwitchBackstop")
    rect("SwX - SwW / 2 - 1 mm", "ChinWall + SwD", "SwX + SwW / 2 + 1 mm", "ChinWall + SwD + RibT")
    c("sketch.finish")
    c("solid.extrude", distance="SwT", operation="join", targets=[SHELL], name="Backstop")
    c("sketch.create", plane="XY", offset="BackWall + SwT / 2 - PlungerH / 2", name="SwitchSlot")
    rect("SwX - PlungerW / 2", "-1 mm", "SwX + PlungerW / 2", "ChinWall + 0.1 mm")
    c("sketch.finish")
    c("solid.extrude", distance="PlungerH", operation="cut", targets=[SHELL], name="SwitchSlotCut")

    # Rear pinhole over the XIAO's reset button (mounting A: the buttons face the back).
    c("sketch.create", plane="XY", name="Pinhole")
    c("sketch.circle.center", center=["PinX", "PinY"], diameter=1.2)
    c("sketch.dimension", entities=["c1"], type="diameter", value="PinD")
    c("sketch.finish")
    c("solid.extrude", distance="BackWall", operation="cut", targets=[SHELL], name="PinholeCut")

    # USB-C notch through the back and bottom walls (and the ledge): the receptacle's face is
    # flush with the bottom edge and its body ends at the back face.
    c("sketch.create", plane="XY", name="UsbNotch")
    rect("UsbCX - UsbW / 2 - Clear", "-1 mm", "UsbCX + UsbW / 2 + Clear", "UsbLen + Clear")
    c("sketch.finish")
    c("solid.extrude", distance="ShellH + SheetT", operation="cut", targets=[SHELL], name="UsbNotchCut")

    # Front sheet: modelled for fit checks and the STEP; it is laser cut, not printed.
    c("sketch.create", plane="XY", offset="ShellH", name="SheetOutline")
    rounded_rect("SheetLip + SheetGap", "SheetLip + SheetGap", "CaseW - SheetLip - SheetGap", "CaseH - SheetLip - SheetGap",
                 "CornerR - SheetLip - SheetGap", 1)
    c("sketch.finish")
    c("solid.extrude", distance="SheetT", operation="new", name="Sheet", body_name="FrontSheet")

elif not SQUARE:
    # Pinhole through the back wall, over one of the XIAO's buttons.
    c("sketch.create", plane="XY", name="Pinhole")
    c("sketch.circle.center", center=["PinX", "PinY"], diameter=1.2)
    c("sketch.dimension", entities=["c1"], type="diameter", value="PinD")
    c("sketch.finish")
    c("solid.extrude", distance="BackWall", operation="cut", targets=[SHELL], name="PinholeCut")

    # USB-C: the receptacle sits in a notch through the back wall and the side wall, its face
    # flush with the outside, so a cable's plug (whose grip stays outside the case) seats fully.
    c("sketch.create", plane="XY", name="UsbNotch")
    rect("XiaoX + XiaoW - (UsbLen - UsbOver) - Clear", "UsbCY - UsbW / 2 - Clear", "CaseW + 1 mm", "UsbCY + UsbW / 2 + Clear")
    c("sketch.finish")
    c("solid.extrude", distance="ShellH", operation="cut", targets=[SHELL], name="UsbNotchCut")

elif MOUNT_B:
    # USB-C out of the bottom edge: an opening in the bottom wall above the flipped board's
    # underside (the back stays closed), and a pocket under the front frame further down.
    c("sketch.create", plane="XY", offset="BackWall + XiaoGap - Clear", name="UsbOpening")
    rect("UsbCX - UsbW / 2 - Clear", "-1 mm", "UsbCX + UsbW / 2 + Clear", "ChinWall + 0.5 mm")
    c("sketch.finish")
    c("solid.extrude", distance="ShellH", operation="cut", targets=[SHELL], name="UsbOpeningCut")

# Front frame: a plate on the shell with the window cut through it.
if not ACRYLIC:
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

    if MOUNT_B:
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


if ACRYLIC:
    # The USB-C notch splits the bottom edge at both the back face and the tray's top.
    c("solid.fillet", edges=outline(0, bottom_split=True), radius="BackR", body=SHELL, name="BackEdgeFillet")
    c("solid.fillet", edges=outline(v["ShellH"] + v["SheetT"], bottom_split=True), radius="RimR", body=SHELL, name="LipFillet")
else:
    top = v["ShellH"] + v["FrontWall"]
    c("solid.fillet", edges=outline(top), radius="FrontR", body="FrontFrame", name="FrontEdgeFillet")
    c("solid.fillet", edges=outline(v["ShellH"], bottom_split=SQUARE), radius="SeamR", body="FrontFrame", name="FrameSeamFillet")
    c("solid.fillet", edges=outline(v["ShellH"], right_split=not SQUARE, bottom_split=SQUARE), radius="SeamR", body="BackShell", name="ShellSeamFillet")
    c("solid.fillet", edges=outline(0, right_split=not SQUARE), radius="BackR", body="BackShell", name="BackEdgeFillet")
    wx, wy, ww, wh = v["WinX"], v["WinY"], v["WinW"], v["WinH"]
    c("solid.chamfer", edges=[[wx + ww / 2, wy, top], [wx + ww / 2, wy + wh, top], [wx, wy + wh / 2, top], [wx + ww, wy + wh / 2, top]],
      distance="WinChamfer", body="FrontFrame", name="WindowChamfer")

c("inspect.measure")

out = Path(__file__).with_name("magnet_case" + ("_acrylic" if ACRYLIC else "_compact" if SQUARE else "")
                               + ("_discs" if STYLE == "discs" and not ACRYLIC else "") + ".json")
out.write_text(json.dumps(cmds, indent=1) + "\n")
print(f"wrote {out} ({len(cmds)} commands, {len(PARAMS)} parameters)")

if ACRYLIC:
    # Cut file for the sheet and the vinyl mask, seen from the back (the vinyl goes on the back,
    # so the window is mirrored left-right). Red: sheet outline (laser). Blue: mask window (vinyl).
    def rr_path(x, y, w, h, r):
        return (f"M{x + r:.3f},{y:.3f} H{x + w - r:.3f} A{r:.3f},{r:.3f} 0 0 1 {x + w:.3f},{y + r:.3f} "
                f"V{y + h - r:.3f} A{r:.3f},{r:.3f} 0 0 1 {x + w - r:.3f},{y + h:.3f} H{x + r:.3f} "
                f"A{r:.3f},{r:.3f} 0 0 1 {x:.3f},{y + h - r:.3f} V{y + r:.3f} A{r:.3f},{r:.3f} 0 0 1 {x + r:.3f},{y:.3f} Z")
    ins = v["SheetLip"] + v["SheetGap"]                # the sheet sits in the lip's pocket
    SW, SH, SR = W - 2 * ins, H - 2 * ins, R - ins
    wx_back = SW - (v["WinX"] - ins) - v["WinW"]       # mirrored for the back, in sheet coordinates
    wy_svg = SH - (v["WinY"] - ins) - v["WinH"]        # SVG y runs down
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW:.3f}mm" height="{SH:.3f}mm" viewBox="0 0 {SW:.3f} {SH:.3f}">\n'
           f'<!-- Acrylic-front case: sheet {SW:.2f} x {SH:.2f} mm, corner R {SR:.2f}, {v["SheetT"]:g} mm thick. Red: cut the sheet. '
           f'Blue: the mask window, {v["WinW"]:.2f} x {v["WinH"]:.2f} mm; seen from the back (vinyl on the back, window mirrored). '
           f'Generated by build_case.py acrylic. -->\n'
           f'<path d="{rr_path(0, 0, SW, SH, SR)}" fill="none" stroke="#ff0000" stroke-width="0.01"/>\n'
           f'<rect x="{wx_back:.3f}" y="{wy_svg:.3f}" width="{v["WinW"]:.3f}" height="{v["WinH"]:.3f}" fill="none" '
           f'stroke="#0000ff" stroke-width="0.01"/>\n</svg>\n')
    svg_out = Path(__file__).with_name("acrylic_sheet.svg")
    svg_out.write_text(svg)
    print(f"wrote {svg_out} (case {W:.2f} x {H:.2f}; sheet {SW:.2f} x {SH:.2f} R {SR:.2f}, window {v['WinW']:.2f} x {v['WinH']:.2f} at {wx_back:.2f}, {wy_svg:.2f} from the top left, seen from the back)")
