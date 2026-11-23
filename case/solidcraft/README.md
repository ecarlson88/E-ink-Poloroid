# Case v0 in SolidCraft

A native, parametric SolidCraft design of layout v1 (`../layout_v1.png`), built by script
with SolidCraft 0.22.0's command-line tool. Unmeasured: every size comes from the
datasheets (`docs/case-dimensions.md`).

## Compact version, 3:4 picture (Erik's choice, mounting B)

`magnet_case_compact.*` (bars) and `magnet_case_compact_discs.*` (discs), with `back_shell_compact.stl`,
`back_shell_compact_discs.stl` and `front_frame_compact.stl`. **64.6 x 96.5 x 6.85** (14.3 mm shorter
than v1). Layout: `../layout_compact.png`. Build: `python3 build_case.py compact [discs]`.

- **Picture:** the window is 50.6 x 67.5 (3:4, `PicRatio` = 4/3, a parameter with no unit:
  1 = square, ~1.5 = full screen) at the top of the panel. The frame covers the bottom
  ~9 mm of the screen, so the chin (bottom edge to picture) is 22.7 mm, 24% of the
  height. A real Polaroid's is ~21%.
- **XIAO:** stands upright at the right, 14.9 mm of it behind the bottom of the panel,
  **flipped so its parts face the front**. Its pads face the back with 0.75 mm (`XiaoGap`)
  for clearance and wire joints.
- **USB-C:** points down, its face flush with the bottom edge. It goes through an opening
  in the bottom wall (the back stays closed) and 0.3 mm into a pocket under the front
  frame, 0.6 of frame left over it; the frame's lip is notched there.
- **Pinhole:** 1.2 mm, through the front of the chin over a XIAO button (`PinX`/`PinY`;
  check which one is reset).
- **Inside:** only the left cross rib; the XIAO takes the right one's place. Bars: six
  on the left, five on the right above the XIAO (`MagBottomR`). Discs: the lower right
  one moves above the XIAO (`DiscLowYR`).
- **Checked:** both build, 0 interferences, and changing PicRatio, XiaoGap and CornerR
  together rebuilt every feature with face counts unchanged.
- **Renders:** `render_compact_front.png`, `render_compact_face.png`,
  `render_compact_back.png`, `render_compact_inside.png`,
  `render_compact_inside_discs.png`.
- **Still to do:** a slot in the chin for the antenna (its socket ends up behind the
  panel, so route its cable down); the server cropping photos to 3:4.

## Acrylic-front version (an additional case type; mounting A)

`magnet_case_acrylic.*`, with `tray_acrylic.stl`, `chin_strip_acrylic.stl`, `front_sheet_acrylic.stl` (for fit checks only) and
`acrylic_sheet.svg`. **Discs only** (Erik: his 8 mm discs; no bar version of this case).
**62.9 x 95.7 x 7.15**. Layout: `../layout_acrylic.png`. Build: `python3 build_case.py acrylic`.
Spec: `docs/superpowers/specs/2026-11-22-acrylic-front-case-design.md`.

- **Front:** a 1 mm clear acrylic sheet over the whole front (`SheetT`), glass-ready: flat, no
  holes or pockets. A white vinyl mask (`MaskT` 0.1) on its back leaves the same 3:4 window as
  the compact case (50.6 x 67.5) and hides the panel's border, so there is no printed frame.
- **Bond stack:** the vinyl covers the whole back of the sheet except the window, so it lies on
  the rim too. The tray's rim, rib and ledge stop `MaskT + TapeT` (0.1 + 0.25) below the sheet
  (`BondZ` 5.80), so with the tape the case is still **7.15** overall. Measure your tape and set
  `TapeT`; `python3 check_acrylic_stack.py` checks the stack in the built model.
- **Lip (Erik):** the sheet drops into a pocket: a 0.8 lip (`SheetLip`) flush with the sheet's
  face, 0.15 fit gap (`SheetGap`) all round. It protects the acrylic's (or later glass's) edges,
  locates the sheet and hides the tape. The sheet is 61.0 x 93.8 with **square corners**, in a
  square pocket (Erik); the case's outer corners are **R 0.8** (`CornerR`; keep `BackR` 0.8 no
  larger than it), and the cavity inside is square. Print a test
  corner to check the fit. Keep `SheetLip + SheetGap` below `ChinWall` (1.0): along the bottom the
  chin ledge carries the sheet, so the case only grows at the sides and top.
- **`acrylic_sheet.svg`:** red is the sheet outline (laser cut), blue is the mask window (vinyl
  cutter). It is drawn **seen from the back**, because the vinyl goes on the back of the sheet.
- **Tray:** one FDM print, back on the bed, no supports. Side and top walls 2.15 (`Wall` =
  1.2 rim `RimW` + gap + lip), bottom 1.0 (`ChinWall`, so the slim antenna clears the cable fold),
  back 1.0. The rim, the left rib and the chin strip carry the sheet (through the mask and the tape).
  The tray prints with **no supports**: its only overhangs are a 0.2 strip under the bottom lip and
  the 1.6 top of the plunger slot.
- **Chin strip (`chin_strip_acrylic.stl`):** a separate flat part, 45 x 4.7 x 0.8 (`LedgeT`),
  printed flat on the bed. It runs across the chin under the sheet (tape area) from the left wall
  to the USB-C notch, and the antenna sticks to its back. It rests on a 0.4 step (`StripStep`) cut
  into the bottom and left walls, with a 0.1 fit gap (`StripGap`); glue it to the step (CA).
  (As part of the tray it was a 4.3 mm shelf over open air, which would need supports.)
- **XIAO, mounting A:** upright at the right, parts and buttons facing the back, `XiaoGap` 0.65
  (0.45 for joints plus 0.2 clearance: the mask took 0.1). The USB-C sits in a notch through the
  back and bottom walls, its face flush with the bottom edge and its body ending at the back face.
- **Rear pinhole** (`PinX`/`PinY`, 1.2) over the XIAO's button nearer the right edge (mounting A
  mirrors the buttons; check which one is reset on the real board). It leaves about 0.55 mm of
  back wall between it and the USB-C notch, as in layout v1.
- **Setup switch (D5):** a side-actuated switch on the back wall at `SwX` 12, pressed upward
  through a plunger slot in the bottom wall (`PlungerW` x `PlungerH`), with a backstop rib behind
  it. `SwW`, `SwD`, `SwT` and the slot are **placeholders until the part is chosen**.
- **Antenna (Erik: option A):** the slim 44 x 4.5 FPC antenna sticks to the back of the chin
  strip, left of the USB-C notch (x 2.4 to 46.5), 4.8 from the back face (not modelled; see `../layout_acrylic.py`).
- **Magnets:** six of Erik's 8 mm discs (measured 0.6 thick), glued into pockets flush with the
  inside of the back wall (`BackWall` = 0.4 skin + 0.6 disc), two per side: just above the chin
  (on the right, above the XIAO), at mid-height and 9 mm below the top edge
  (`render_acrylic_inside.png`). Same pole facing out on all six.
- **Checked** (SolidCraft CLI and the parametric-3d-parts skill's `verify.py`): both build, 0
  interferences; changing XiaoGap, CornerR and SheetGap together rebuilt all 26 features with face counts
  unchanged (also with StripStep 0.5 and StripGap 0.15) (verify.py's merged face count moves by one there:
  coplanar faces that happen to touch at the defaults).
  `check_acrylic_stack.py` passes (lip flush, sheet inset 0.95, rim 5.80, overall 7.15).
  Not opened in the desktop app.
- **Assembly:** antenna onto the back of the chin strip, glue the strip onto its step; thin VHB tape on
  the rim, the rib and the strip, then drop the sheet into the lip (warm it to open the case); vinyl
  on the back of the sheet before fitting; foam pads behind the panel as in the compact case;
  no acetic-cure silicone near the panel. The 0.4 skin over each magnet is two FDM layers:
  print a test patch first.
- **Renders:** `render_acrylic_inside.png` (sheet hidden), `render_acrylic_back.png`,
  `render_acrylic_edge.png` (bottom edge: plunger slot and USB-C notch),
  `render_acrylic_chin.png` (bottom-left corner, strip hidden: slot, strip step, rib, backstop), `render_acrylic_lip.png`
  (top-left corner: the sheet in the lip).
- **Unmeasured:** everything from the datasheets, as for the other versions, plus the switch.

## Layout v1 (full screen)

Two magnet options, same everything else:

- **Bars** (`magnet_case.*`, `back_shell.stl`): 12 x 8x3x1 bars on raised pads along the side walls.
- **Discs** (`magnet_case_discs.*`, `back_shell_discs.stl`): 6 of Erik's own 8 mm discs, measured
  0.6 thick, in pockets flush with the inside of the back wall (`BackWall = MagSkin + MagT`),
  so nothing stands proud inside and they sit at the top corners (behind the battery), at
  mid-height and just above the chin. A thicker disc thickens the back wall to match: 0.8 mm
  discs make the case 7.05.

`front_frame.stl` is the same for both.

| File | What |
|---|---|
| `magnet_case.solidcraft` | **Open this in SolidCraft.** Editable history: 17 sketches and features, 63 named parameters |
| `magnet_case.step` | Both bodies, for Fusion or anything else (fixed solids, no history) |
| `back_shell.stl`, `front_frame.stl` | Print files, one per part |
| `magnet_case.json` | The SolidCraft script that builds the design |
| `build_case.py` | Writes `magnet_case.json` (or `magnet_case_discs.json` with `discs`); the parameter list with comments lives here |
| `render_front.png`, `render_back.png`, `render_inside.png`, `render_inside_discs.png`, `render_detail.png` | Renders from the SolidCraft CLI (inside: front frame hidden; detail: window chamfer and edge fillets) |

## Two parts

- **BackShell**: an open tray, 64.6 x 110.8 x 5.85. Inside it:
  - 12 pockets for 8 x 3 x 1 magnet bars, six upright along each side wall, from above
    the chin to below the top corners, opened from the inside, leaving a 0.4 mm skin to
    the fridge;
  - a 1.2 mm pinhole over one of the XIAO's buttons;
  - a notch through the back and the right side for the USB-C receptacle, its face flush with the outside;
  - two cross ribs (1.2 thick, `RibT`) from the back wall up to the frame, just below the
    panel's bottom edge, either side of a 30 mm centre gap (`RibGap`) for the panel cable's
    fold and the wires. They support the frame across its middle (a second glue line),
    stop the panel's bottom edge and stiffen the shell. They stop 0.15 mm short of the
    frame's lip at each end.
- **FrontFrame**: a 1.0 mm plate with the window (active area minus 0.5 mm per side) and a
  0.6 mm locating lip that drops inside the shell walls with 0.15 mm clearance.
- **Edge finishing** (`render_detail.png`):
  - 0.45 mm fillet on the front face's outer edge (`FrontR`). SolidCraft 0.22 refuses more
    than ~0.5 on the 1 mm frame ("not supported yet").
  - 0.8 mm fillet on the back face's outer edge (`BackR`).
  - 0.3 mm on both edges of the frame/shell seam (`SeamR`), leaving a small groove that
    hides the glue line.
  - A 0.6 mm x 45 degree chamfer around the window on the front face only (`WinChamfer`),
    so the panel side of the window, and the masking, are unchanged.
  - The USB-C notch and pinhole edges are left sharp.

Overall 64.6 x 110.8 x 6.6 (with Erik's measured XIAO: 2.8 without the USB-C, 4.4 with it, and 0.75 mm under it for clearance plus joints, `XiaoGap`).

## Changing sizes

In SolidCraft, open the **Parameters** panel and change a value. The derived sizes
(`CaseW`, `ChinH`, `InnerD`, window, XIAO, pinhole and magnet positions) are expressions
and rebuild with it. Checked here: changing MagL, MagW, XiaoBodyT and AAW together rebuilt every feature without
errors (an earlier check with the disc magnets changed six values at once). With a 2 mm XIAO the case drops to 6.6
mm, because the panel and battery then set the depth.

Check that the parts don't overlap after a change: run `inspect.interference` (SolidCraft's
Inspect menu, or `solidcraft-cli run` with `[{"command": "inspect.interference", "params": {}}]`).
Both versions report 0. It caught the first rib version running into the frame's lip.

One limit: the magnet boss height is `MagSkin + MagT - BackWall`. If the magnets are
thinner than `BackWall - MagSkin` (0.6 mm), that height is zero or negative and the
`Bosses` feature fails. Thin the back wall or drop the boss in that case. The number of bars
per side (`MAG_ROWS`, 6) is set in `build_case.py`; their spacing follows the parameters.

Rebuild from the script (after editing `build_case.py`):

    python3 build_case.py
    solidcraft-cli run magnet_case.json --save magnet_case.solidcraft --out magnet_case.step

## Not in v0 yet

- **Holding the panel against the frame:** nothing yet. It needs ribs or foam from the back.
- **How the two parts stay together:** only the lip locates them, so they need glue, clips
  or screws.
- **Inside the case:**
  - a guide tube for the pinhole;
  - a pocket for the antenna;
  - cable routing;
  - fillets on the outer edges.
- **Not opened in the SolidCraft desktop app:** this container has no screen. The design
  was built, rebuilt with changed parameters, exported and rendered by `solidcraft-cli`.

## What SolidCraft 0.22 was like for this

- **Edges are picked by a point** (plain numbers, no expressions), then **kept by
  geometry.** The fillets and chamfer survived parameter changes that moved their edges:
  XiaoBodyT, SideFrame, CornerR and the active area changed together, every feature
  rebuilt, the face counts were unchanged and there were no interferences.
- **`tangent_chain` was silently ignored** on fillets, so each rounded outline is listed
  edge by edge (4 lines + 4 arcs, computed in `build_case.py`).

- **Scripting works well.** `solidcraft-cli commands` documents every command's parameters,
  and its error messages point at the exact step and field.
- **Parameter expressions** (including `max()`) work in parameters, sketch-plane offsets,
  line points, dimensions and extrude distances.
- **Not every command takes an expression.** The rectangle and circle commands take
  only plain numbers, so outlines are drawn as lines with expression points and then
  rounded with `sketch.fillet`. Circles take a dimension tied to a parameter.
- **Running with `--in design.solidcraft`** left a `.bak` next to the design. The design's
  parameters were unchanged.
- **Rendering here used the CPU fallback** (no GPU), which still gives usable pictures.
