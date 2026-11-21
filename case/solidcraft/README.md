# Case v0 in SolidCraft

A native, parametric SolidCraft design of layout v1 (`../layout_v1.png`), built by script
with SolidCraft 0.22.0's command-line tool. Unmeasured: every size comes from the
datasheets (`docs/case-dimensions.md`).

| File | What |
|---|---|
| `magnet_case.solidcraft` | **Open this in SolidCraft.** Editable history: 17 sketches and features, 63 named parameters |
| `magnet_case.step` | Both bodies, for Fusion or anything else (fixed solids, no history) |
| `back_shell.stl`, `front_frame.stl` | Print files, one per part |
| `magnet_case.json` | The SolidCraft script that builds the design |
| `build_case.py` | Writes `magnet_case.json`; the parameter list with comments lives here |
| `render_front.png`, `render_back.png`, `render_inside.png` | Renders from the SolidCraft CLI (inside: front frame hidden) |

## Two parts

- **BackShell**: an open tray, 64.6 x 110.8 x 5.85. Inside it:
  - 12 pockets for 8 x 3 x 1 magnet bars, six upright along each side wall, from above
    the chin to below the top corners, opened from the inside, leaving a 0.4 mm skin to
    the fridge;
  - a 1.2 mm pinhole over one of the XIAO's buttons;
  - a notch through the back and the right side for the USB-C receptacle, its face flush with the outside.
- **FrontFrame**: a 1.0 mm plate with the window (active area minus 0.5 mm per side) and a
  0.6 mm locating lip that drops inside the shell walls with 0.15 mm clearance.

Overall 64.6 x 110.8 x 6.85.

## Changing sizes

In SolidCraft, open the **Parameters** panel and change a value. The derived sizes
(`CaseW`, `ChinH`, `InnerD`, window, XIAO, pinhole and magnet positions) are expressions
and rebuild with it. Checked here: changing MagL, MagW, XiaoBodyT and AAW together rebuilt every feature without
errors (an earlier check with the disc magnets changed six values at once). With a 2 mm XIAO the case drops to 6.6
mm, because the panel and battery then set the depth.

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
