# Acrylic-front case with an edge setup button (prototype, XIAO build)

Status: approved by Erik in conversation, 2026-11-22. A short design: an additional case type for the
current XIAO ESP32-S3 prototype. The v1 and compact cases stay as they are; nothing is removed.

## Intent
Erik wants to try a more finished look on the current prototype, which is also a step toward the
production-style case of the custom-PCB phase (`docs/phase2-custom-pcb.md`). A flat sheet over the
whole front, with a printed or vinyl mask that leaves the 3:4 picture clear, looks like a finished
product rather than a printed frame. It also gives the panel the protective cover its datasheet asks for.

## Goals
- A new case type: a 1 mm clear sheet on the front, one FDM-printed tray behind it.
- Built for **acrylic** now (Erik: "I'll probably just go acrylic"), but dimensioned so a 1 mm
  glass sheet can replace it with no CAD change: no pockets, holes or engraving in the sheet.
- A dedicated **setup button on the bottom edge of the chin**, wired to D5, replacing the pinhole as
  the parents' way into setup mode.
- Keep a **rear pinhole to the XIAO's reset button** as a backup restart (the battery is soldered,
  so a frozen magnet could otherwise only be restarted by opening the case).

## Non-goals
- No change to the v1 or compact cases, their CAD or their STLs.
- No change to the server.
- No custom PCB work (that is a separate design, still to be written).

## Anti-goals
- A sheet design that only works in acrylic (would block the later glass version).
- A setup control that triggers by accident when the fridge is wiped or the door slams.

## Approaches considered
1. **Chosen: mounting A, 7.15 mm.** The XIAO faces the back (as in layout v1): the USB-C sits flush in
   a notch through the back wall and the reset button is reachable through a rear pinhole. Works with
   acrylic or glass.
2. Mounting B on acrylic, 6.85 mm: a 0.3 mm laser-engraved pocket in the back of the acrylic takes
   the USB-C, as the printed front frame does today. Rejected: the reset button would face the
   acrylic (no backup restart), and glass could not take the pocket.
3. Other setup controls, rejected for the prototype: capacitive touch through the sheet on D5 (sleep
   current unknown, false triggers when wiping, and the ESP32-C6 planned for the custom board has no
   touch sensor; worth a bench test in Task 1), a Hall sensor and a magnet (12 neodymium bars and a
   steel door nearby), a motion gesture (depends on the optional Task 8, hard to discover).

Why 7.15 and not 6.85: in mounting B the USB-C borrows 0.3 mm of the printed front wall; a flat sheet
cannot lend it, so the inside must hold the full XIAO stack, 0.75 joint gap + 4.4 = 5.15 mm, and
1 + 5.15 + 1 = 7.15. Mounting A already needs 7.15 today (`case/layout_compact.py`).

## Decisions (Erik's)
- Front: 1 mm sheet, acrylic for the prototype; glass later must drop in.
- Tray: FDM printed (Erik prints).
- Setup: edge button on D5. **Short press: show the next photo. Hold 5 s: setup mode.**
- Mounting A, rear reset pinhole kept; design thickness 7.15 mm.
- An additional case type; existing models kept.

## Design
- **Front sheet:** 1.0 mm clear acrylic, laser cut to the case outline, corners rounded to match the
  tray. A white vinyl mask (about 0.1 mm) on its back leaves the picture window clear: the same 3:4
  window, position and 0.5 mm overlap onto the active area as the compact case (picture 50.6 x 67.5).
  The mask covers the panel's inactive border, so the tray no longer needs the 3 mm front frame.
- **Tray:** one FDM print, printed back-down (smooth fridge side, no supports). Side, top and bottom
  walls about 1.2 mm (three 0.4 mm perimeters). The sheet bonds to the tray's top rim and to the
  chin area with thin VHB tape, which can be warmed and peeled to open the case. Outline about
  **61 x 95 x 7.15 mm** (today's compact: 64.6 x 96.5 x 6.85): width 58 + 2 x (0.3 + 1.2) = 61.0;
  height 7.6 (chin below the panel, unchanged) + 85.64 + 0.3 + 1.2 = 94.7.
- **Panel:** lies against the back of the sheet (mask between), held by foam pads behind it, as in
  the compact case's ruling. Panel cable folds behind it as today.
- **XIAO:** upright at the right behind the bottom of the panel, as in the compact layout, but in
  mounting A: parts and buttons face the back, battery pads and wire joints face the panel with the
  0.75 mm `XiaoGap`. USB-C points down, face flush with the bottom edge, body in a notch through the
  back wall (it must end at or inside the back face).
- **Rear pinhole:** 1.2 mm through the back wall over the XIAO's reset button (the compact model's
  button positions; which of the two is reset is still to be checked on the real board).
- **Edge button:** a low-profile side-actuated tactile switch in the chin, left of the XIAO, its
  plunger through a hole in the bottom wall. Wired D5 to GND, internal pull-up, wakes the ESP32-S3
  from deep sleep. Placed so it leaves room for the antenna in the chin.
- **Magnets:** the 12 bars (and the discs variant) as in the compact case, in pockets with a 0.4 mm
  skin. Risk: with 1.2 mm walls the strip between the side wall and the 50 mm battery is about
  4.3 mm, against a 4.2 mm bar pad plus 0.5 mm clearance. The model asserts it; if it fails, the
  case grows about 1 mm wider or the bars shrink to a 2 mm width (Erik to choose then).
- **Firmware:** D5 becomes the setup button in the pin map (`docs/plan.md`). A new pure function in
  `logic.c`, tested on the PC first, turns how long the button was held into an action (next photo or
  setup mode); `SETUP_HOLD_MS` = 5000 in `settings.h`. The reset double-press path (`boot_action`)
  stays as it is.

## Left to the builder
- The switch part (side-actuated, roughly 1.5 to 2 mm tall) and its hole size.
- The exact bonding rim width (more rim means a wider or taller case).
- Which deep-sleep wake the D5 button uses alongside the MPU6050 interrupt on D9 (EXT0 for one and
  EXT1 for the other, or both on EXT1 with the same active level).
- File names follow the existing pattern: `case/layout_acrylic.py` (+ `.png`), `build_case.py acrylic
  [discs]`, `case/solidcraft/magnet_case_acrylic*`, `tray_acrylic*.stl`, a 2D outline for the sheet and
  mask (DXF or SVG) for laser and vinyl cutters.

## Constraint found while writing this
SolidCraft (`solidcraft-cli`), which builds and checks the existing CAD, is not installed in this
cloud session. `build_case.py` can write the new script here, but building the STEP/STL files and the
interference check must run where SolidCraft is installed.
