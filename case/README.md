# Case (Task 7)

`layout.py` draws the proposed layout to scale (`layout_v0.png`) from the numbers in
`docs/case-dimensions.md`. Rerun it after measuring the parts: `python3 case/layout.py`
(needs matplotlib).

## Layout v0 (proposal, datasheet numbers, unmeasured)

About **64.6 x 110.8 x 7.1 mm**.

- **Panel** at the top, behind a front frame 3 mm wide at the sides and top. The frame
  covers the panel edge and overlaps the active area by 0.5 mm per side (the masking idea).
- **Panel cable** folds back 180° under the bottom edge of the panel.
- **Adapter** (pin header removed) lies behind the lower middle of the panel, its
  connector facing down to take the folded cable.
- **Battery** lies sideways (50 x 34) behind the upper part of the panel. It fits with
  about 0.2 mm to spare at the top, so the measured sizes matter.
- **Chin** (~21.6 mm) holds the XIAO lying flat. Its USB-C points out of the right edge,
  with the connector face flush with the outside of the case. Pointing it down would make
  the chin about 27 mm.
- **Antenna** runs along the chin near the front, away from the steel door. Its size is
  still unknown.
- **Setup button** on the bottom edge of the chin, on the left.
- **Magnets:** 4 x 8x1 discs in the back wall corners.
- **Depth:** 1.0 front wall + 1.0 panel + 3.0 battery/adapter (+0.6 clearance) + 1.0 back
  wall. The XIAO (4.5 including USB-C) sets the chin's depth.

## Open before CAD

- Measured sizes: panel visible area (50.4 x 75.6 or 51.6 x 77.04), adapter thickness
  with the header removed, where the battery leads leave, and the antenna's size.
- Whether the panel cable fits the adapter at all (`docs/case-dimensions.md`, section 2).
