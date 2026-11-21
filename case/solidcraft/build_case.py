"""Writes magnet_case.json, a SolidCraft script that builds the case v0 as a parametric
design: every size is a named parameter (Parameters panel), derived sizes are
expressions of them, and sketches follow the parameters when they change.

Layout and numbers: case/layout.py and docs/case-dimensions.md (datasheets, unmeasured).

Build (from this folder, SolidCraft 0.22):
    python3 build_case.py
    solidcraft-cli run magnet_case.json --save magnet_case.solidcraft --out magnet_case.step

Coordinates (mm): x to the right and y up as seen from the front, z from the back face
(on the fridge, z = 0) toward the front. Two bodies: BackShell (an open tray) and
FrontFrame (the front plate with the window and a locating lip).
"""
import json
from pathlib import Path

# name, expression, comment. Plain values are measured or chosen; the rest are derived.
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
    ("XiaoBodyT", "3.25 mm", "XIAO height without the USB-C (STEP model; Erik estimates ~2: measure)"),
    ("Joint", "1 mm", "battery wire joints on the XIAO underside pads (guess)"),
    ("UsbOver", "1.5 mm", "USB-C overhang past the XIAO edge"),
    ("UsbW", "8.9 mm", "USB-C receptacle width"),
    ("UsbLen", "7.3 mm", "USB-C receptacle length including the overhang"),
    ("BtnFromEnd", "1.6 mm", "XIAO button centre from the USB-C end of the board"),
    ("BtnFromSide", "3 mm", "XIAO button centre from a long edge"),
    ("MagD", "8 mm", "magnet diameter (Erik to measure)"),
    ("MagT", "1 mm", "magnet thickness (Erik to measure)"),
    # Case choices
    ("Clear", "0.3 mm", "gap around parts"),
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
    ("LipW", "0.8 mm", "front frame locating lip width"),
    ("LipH", "0.6 mm", "front frame locating lip height"),
    ("LipGap", "0.15 mm", "lip clearance to the shell wall"),
    # Derived
    ("CaseW", "PanelW + 2 * (SideFrame + Clear)", "overall width"),
    ("ChinH", "Fold + XiaoH + 2 * Clear + ChinWall", "chin height"),
    ("CaseH", "ChinH + PanelH + 2 * Clear + TopFrame", "overall height"),
    ("InnerD", "max(PanelT + max(BattT, AdapterT), Joint + XiaoBodyT) + 2 * Clear", "inside depth"),
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
    ("PinX", "XiaoX + XiaoW - BtnFromEnd", "pinhole x (over a XIAO button)"),
    ("PinY", "XiaoY + BtnFromSide", "pinhole y (the lower button: check which is reset)"),
    ("AdapterY", "PanelY + FpcLen - Fold - 3 mm", "adapter bottom edge (folded cable end)"),
    ("MagX", "PanelX + (PanelW - AdapterW) / 4", "magnet column x (beside the adapter)"),
    ("MagY1", "AdapterY + 6 mm", "lower magnet row"),
    ("MagY2", "AdapterY + AdapterH - 6 mm", "upper magnet row"),
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

# Magnet bosses on the inside of the back wall, then pockets from the inside, leaving MagSkin.
mags = [("MagX", "MagY1"), ("CaseW - MagX", "MagY1"), ("MagX", "MagY2"), ("CaseW - MagX", "MagY2")]
c("sketch.create", plane="XY", offset="BackWall", name="MagnetBosses")
for i, (mx, my) in enumerate(mags, start=1):
    c("sketch.circle.center", center=[mx, my], diameter=10)
    c("sketch.dimension", entities=[f"c{i}"], type="diameter", value="MagD + MagGap + 2 * BossWall")
c("sketch.finish")
c("solid.extrude", distance="MagSkin + MagT - BackWall", operation="join", targets=["BackShell"], name="Bosses")

c("sketch.create", plane="XY", offset="MagSkin + MagT", name="MagnetPockets")
for i, (mx, my) in enumerate(mags, start=1):
    c("sketch.circle.center", center=[mx, my], diameter=8)
    c("sketch.dimension", entities=[f"c{i}"], type="diameter", value="MagD + MagGap")
c("sketch.finish")
c("solid.extrude", distance="MagT", direction="negative", operation="cut", targets=["BackShell"], name="Pockets")

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

c("inspect.measure")

out = Path(__file__).with_name("magnet_case.json")
out.write_text(json.dumps(cmds, indent=1) + "\n")
print(f"wrote {out} ({len(cmds)} commands, {len(PARAMS)} parameters)")
