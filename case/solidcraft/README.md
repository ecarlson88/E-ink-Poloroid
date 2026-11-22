# Case v0 in SolidCraft

A native, parametric SolidCraft design of layout v1 (`../layout_v1.png`), built by script
with SolidCraft 0.22.0's command-line tool. Unmeasured: every size comes from the
datasheets (`docs/case-dimensions.md`).

## Square picture version (Erik's choice, mounting B)

`magnet_case_square.*` (bars) and `magnet_case_square_discs.*` (discs), with `back_shell_square.stl`,
`back_shell_square_discs.stl` and `front_frame_square.stl`. **64.6 x 96.5 x 6.85** (14.3 mm shorter
than v1). Layout study: `../layout_square.png`.

- **Picture:** the window is a 50.6 mm square at the top of the panel; the frame masks the
  bottom ~25.9 mm of the screen, which reads as a big Polaroid chin.
- **XIAO:** stands upright at the right, 14.9 mm of it behind the masked strip, **flipped
  so its parts face the front**. Its pads face the back with 0.75 mm (`XiaoGap`) for
  clearance and wire joints.
- **USB-C:** points down, its face flush with the bottom edge. It goes through an opening
  in the bottom wall (the back stays closed) and 0.3 mm into a pocket under the front
  frame, 0.6 of frame left over it; the frame's lip is notched there.
- **Pinhole:** 1.2 mm, through the front of the chin over a XIAO button (`PinX`/`PinY`;
  check which one is reset).
- **Inside:** only the left cross rib; the XIAO takes the right one's place. Bars: six
  on the left, five on the right above the XIAO (`MagBottomR`). Discs: the lower right
  one moves above the XIAO (`DiscLowYR`).
- **Checked:** both build, 0 interferences, and changing XiaoGap, BattT, CornerR and
  UsbLen together rebuilt every feature with face counts unchanged.
- **Renders:** `render_square_front.png`, `render_square_back.png`,
  `render_square_inside.png`, `render_square_inside_discs.png`.
- **Still to do:** a slot in the chin for the antenna (its socket ends up behind the
  panel, so route its cable down); the server cropping photos to the square.

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
