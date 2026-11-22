# Case (Task 7)

**CAD: `solidcraft/`** holds the parametric SolidCraft designs with STEP and STL exports:
the **compact version with a 3:4 picture** (Erik's choice: `layout_compact.py`, mounting B,
64.6 x 96.5 x 6.85) and layout v1 (full screen, 64.6 x 110.8 x 6.6, below) for comparison.
An additional case type, the **acrylic-front version** (`layout_acrylic.py`, `build_case.py acrylic`,
61.0 x 94.7 x 7.15): a 1 mm acrylic sheet with a vinyl mask over one FDM tray, XIAO mounting A,
and a setup button on the bottom edge (D5). See `solidcraft/README.md`.

`layout.py` draws the proposed layout to scale  from the numbers in
`docs/case-dimensions.md`. Rerun it after measuring the parts: `python3 case/layout.py`
(writes `layout_v1.png`)
(needs matplotlib).

## Layout v1 (proposal, datasheet numbers, unmeasured)

About **64.6 x 110.8 x 6.6 mm**.

- **Panel** at the top, behind a front frame 3 mm wide at the sides and top. The frame
  covers the panel edge and overlaps the active area by 0.5 mm per side (the masking idea).
- **Panel cable** folds back 180° under the bottom edge of the panel.
- **Adapter** (pin header removed) lies behind the lower middle of the panel, its
  connector facing down to take the folded cable.
- **Battery** lies sideways (50 x 34) behind the upper part of the panel. It fits with
  about 0.2 mm to spare at the top, so the measured sizes matter.
- **Chin** (~21.6 mm) holds the XIAO lying flat, **upside down** (Erik): the underside
  battery pads and their wire joints face the front wall, the parts face the back. The
  USB-C points out of the right edge, its face flush with the outside, and its body sits
  in a **notch through the back shell**, so the connector does not set the case depth.
  By the STEP model it ends about 0.1 mm inside the back face, so nothing sticks out
  toward the fridge. Pointing the USB-C down would make the chin about 27 mm.
- **Antenna** runs along the chin near the front, away from the steel door. Its size is
  still unknown.
- **No separate setup button** (Erik). Instead a **1.2 mm pinhole in the back** reaches
  one of the XIAO's own buttons, which face the back because the board is upside down.
  They sit 1.6 mm in from the USB-C end and about 3.0 mm in from each long edge (STEP
  model). A paperclip travels about 2.6 mm from the back face to the button; a short
  guide tube from the inside of the back wall would stop it slipping off. **Erik: the
  reset button** (double press = setup mode). Check which of the two buttons is reset on
  the real board; `PinY` in the CAD picks the lower one.
- **Cross ribs** (Erik): two 1.2 mm ribs from the back wall to the frame, just below the
  panel's bottom edge, with a 30 mm centre gap for the panel cable's fold and the wires.
  1.1 mm above the XIAO; the gap clears the 26 mm cable by 2 mm each side.
- **Magnets:** 12 **8 x 3 x 1 bars** (Erik), six upright along each side wall from above
  the chin to below the top corners. They are **glued into pockets** in the back wall,
  open on the inside. Each pocket leaves a 0.4 mm skin on the fridge side and its pad
  stands 0.4 mm proud inside, in the strip between the side wall and the battery or
  adapter (1.9 mm clear of the battery), so they add no thickness. Total magnet area is
  288 mm², about 1.4x the four discs, and it reaches the top edge.
  **Option: Erik's 8 mm discs, measured 0.6 thick** (`layout_v1_discs.png`). Pocket plus 0.4 skin equals
  the 1.0 back wall, so they are flush inside and can go anywhere: six, at the top corners
  (behind the battery), mid-height and just above the chin. 302 mm² of magnet, but a 0.6
  thick magnet pulls less than a 1 mm one: test one on the fridge. Glue: cyanoacrylate or epoxy,
  not acetic-cure silicone, which the panel datasheet warns against.
  None in the chin, which holds the XIAO and the antenna (metal near it detunes it).
  - Size the pockets about 0.2 mm over the magnet and fit them all with the same pole
    facing out.
  - Holding force through a 0.4 mm skin is a little lower than touching.
- **Depth:** 1.0 front wall + inner 4.6 + 1.0 back wall = 6.6. The **panel + battery** stack
  (4.0 + 2 x 0.3 clearance) sets it. Under the XIAO, Erik plans **0.75 mm for clearance plus
  wire joints** (`XiaoGap`), so with 0.3 clearance the joints must be ~0.45 mm or flatter.
  With the measured XIAO (2.8 without the USB-C, 4.4 with it), the USB-C then sits 0.45 mm
  inside the back face. The model also keeps the USB-C from ever sticking out: with
  `XiaoGap` above ~1.2 the USB-C sets the depth instead (1.3 gives 6.7). A thinner battery
  saves nothing more unless the chin is raised.

## Assembly (Erik's choices)

- **Front frame to back shell: glue.** The lip locates the frame and gives a glue
  surface. Use cyanoacrylate or epoxy, not acetic-cure silicone near the panel. Glued
  shut means opening it later (battery, repairs) breaks the case, so do the bench tests
  first.
- **Panel held against the frame: foam.** Behind the panel the gap is about 3.85 mm
  (inner depth 4.8 minus the 1.0 panel). The battery and adapter already fill most of it.
  Put soft foam pads, about 4-5 mm thick before squashing, in the open areas behind the
  panel: beside the adapter (about 16 x 35 mm on each side, inside the magnet pads in
  the bars version) and in the strip under the adapter beside the cable fold. Don't
  press on the battery or the cable fold.

## Open before CAD

- Measured sizes: wire joint height (the XIAO is measured: 2.8 / 4.4; re-check on the
  ESP32-S3 if the measurement was on the nRF52840 stand-in), panel visible area (50.4 x 75.6 or 51.6 x 77.04), adapter thickness
  with the header removed, where the battery leads leave, and the antenna's size.
- Whether the panel cable fits the adapter at all (`docs/case-dimensions.md`, section 2).
