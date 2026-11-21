# Case (Task 7)

**CAD: `solidcraft/`** holds the parametric SolidCraft design (v0) with STEP and STL exports.

`layout.py` draws the proposed layout to scale  from the numbers in
`docs/case-dimensions.md`. Rerun it after measuring the parts: `python3 case/layout.py`
(writes `layout_v1.png`)
(needs matplotlib).

## Layout v1 (proposal, datasheet numbers, unmeasured)

About **64.6 x 110.8 x 6.8 mm**.

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
  guide tube from the inside of the back wall would stop it slipping off. Which button
  (reset or boot) is still to be decided (`docs/ledger.md`).
- **Magnets:** 4 x 8x1 discs **glued into pockets** in the back wall, open on the inside
  (Erik). Each pocket leaves a 0.4 mm skin on the fridge side, so the wall is 1.4 mm
  there and the magnet stands 0.4 mm proud inside. That sits beside the adapter, where
  nothing is behind the panel, so the case stays 6.8 mm. Glue: cyanoacrylate or epoxy,
  not acetic-cure silicone, which the panel datasheet warns against.
  They cannot go in the corners, because the battery fills the top behind the panel
  and the chin holds the XIAO and the antenna (metal near the antenna detunes it).
  - The top ~40 mm has no magnets: check it doesn't lean out from the door
    (Task 7 Step 5).
  - Size the pockets about 0.2 mm over the magnet and fit them all with the same pole
    facing out.
  - Holding force through a 0.4 mm skin is a little lower than touching.
- **Depth:** 1.0 front wall + inner 4.8 + 1.0 back wall. Inside, the XIAO stack sets it:
  ~1.0 wire joints + 3.25 board and shield can (+0.6 clearance). The panel + battery
  side needs 4.0 (+0.6).

## Open before CAD

- Measured sizes: XIAO height without the USB-C (STEP model 3.25, Erik estimates ~2;
  if it is 2, the panel and battery set the depth instead), wire joint height, panel visible area (50.4 x 75.6 or 51.6 x 77.04), adapter thickness
  with the header removed, where the battery leads leave, and the antenna's size.
- Whether the panel cable fits the adapter at all (`docs/case-dimensions.md`, section 2).
