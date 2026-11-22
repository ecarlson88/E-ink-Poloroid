# Acrylic-Front Case and Edge Setup Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** an additional case type for the XIAO prototype (a 1 mm acrylic sheet on a one-piece FDM tray, XIAO mounting A, 7.15 mm) plus an edge setup button on D5 (short press: next photo; hold 5 s: setup mode).

**Architecture:** the case follows the project's existing pattern: a to-scale matplotlib layout with asserts (`case/layout_acrylic.py`), then a parametric SolidCraft design written by `case/solidcraft/build_case.py acrylic [discs]`, built and checked with `solidcraft-cli` and the parametric-3d-parts skill's `verify.py`. The firmware change is one pure function in `logic.c`, tested on the PC; the hardware wiring of it is written into `docs/plan.md` Task 5 for later.

**Tech Stack:** Python 3 + matplotlib (layout), SolidCraft 0.22.0 CLI (CAD; installed by the skill's `scripts/install_solidcraft.sh`, which prints the CLI path), C with gcc (logic tests).

**Spec:** `docs/superpowers/specs/2026-11-22-acrylic-front-case-design.md`

## Global Constraints

- Additional case type: do not change the v1 or compact outputs. `python3 build_case.py`, `... discs`, `... compact`, `... compact discs` must write byte-identical JSON to what they write before this work (check with `git diff --exit-code` on the four JSON files after regenerating them).
- Overall thickness 7.15 mm: sheet 1.0 + inside depth 5.15 + back wall 1.0.
- Front sheet 1.0 mm, flat, no holes, pockets or engraving (so glass can replace it).
- XIAO mounting A: parts and buttons face the back; USB-C points down, face flush with the bottom edge, body in a notch through the back wall, never past the back face.
- Same picture as the compact case: 3:4 (`PicRatio` 4/3), `Mask` 0.5, window at the top of the panel.
- Walls 1.2 (side, top, bottom/chin), back 1.0, clearance 0.3, magnet skin 0.4, pinhole 1.2 (`references/print-design.md` defaults).
- `SETUP_HOLD_MS` = 5000. D5 = GPIO6, active low, internal pull-up.
- Every unmeasured size stays a named parameter with its source in the comment.
- Rulings go in `docs/ledger.md` as `Ruling:` lines with what they cost if wrong (CLAUDE.md).

## Review Focus

1. **The button is stuck down** (jammed against the fridge door seal, or held by a child): the magnet must not wake over and over and drain the battery. Pinned in Task 2's `docs/plan.md` wording (do not re-arm the D5 wake while D5 reads low) and its bench check.
2. **A bump, not a press** (a door slam closes the switch for a few milliseconds): the result must be at most one extra photo, never setup mode. Pinned by Task 2's `button_action(0)` and `button_action(4999)` checks.
3. **Firmware on a compact or v1 case with no button wired:** D5 floats; with the internal pull-up it must never trigger. Pinned in Task 2's `docs/plan.md` wording (pull-up enabled before arming).
4. **The vinyl mask's thickness:** the panel sits ~0.1 mm further back, which must not push the XIAO joints into the panel. Pinned by Task 1's depth assert.
5. **The magnet bosses under the battery:** with the 3 mm frame gone, the bar bosses overlap the battery in plan; they are fine only if the battery clears them in depth. Pinned by Task 1's assert.

---

### Task 1: Layout drawing for the acrylic case

**Files:**
- Create: `case/layout_acrylic.py`, `case/layout_acrylic.png` (generated)

**Interfaces:**
- Produces: the numbers Task 3 models (printed by the script) and the agreed layout.

- [ ] **Step 1: Write `case/layout_acrylic.py`,** starting from `case/layout_compact.py` (same part sizes, `PIC_RATIO`, `MASK`, `XIAO_*`, magnet bars). Changes:
  - `SHEET_T = 1.0`, `MASK_T = 0.1` (vinyl), `WALL = 1.2` on all four sides: `CASE_W = PANEL_W + 2 * (CLEAR + WALL)` (61.0); `CASE_H = panel_y + PANEL_H + CLEAR + WALL` (about 94.7). No `SIDE_FRAME`/`TOP_FRAME`.
  - Mounting A only: `XIAO_GAP = 0.65` (Ruling: the mask's 0.1 comes out of the 0.75 gap's clearance; joint room stays 0.45 with 0.2 clearance to the panel). `INNER = max(MASK_T + PANEL_T + BATT_T + 2 * CLEAR, MASK_T + PANEL_T + XIAO_GAP + XIAO_BODY_T + CLEAR, MASK_T + PANEL_T + XIAO_GAP + XIAO_T - BACK_WALL)`; `T = SHEET_T + INNER + BACK_WALL`.
  - Rear pinhole at `(xiao_x1 - BTN_FROM_SIDE, xiao_y0 + BTN_FROM_END)` (mirror of mounting B's front pinhole).
  - Edge switch, side-actuated, unchosen part: `SW_W, SW_D, SW_T = 3.5, 2.9, 1.6` (placeholder), plunger slot `1.6 x 1.0`; switch body against the bottom wall at `SW_X = 12.0` (centre), on the back wall; a backstop rib `1.2` thick behind it from the back wall to the switch top.
  - Chin bonding ledge: a strip under the sheet across the chin, `LEDGE_T = 0.8` thick, from `y = WALL` to `panel_y - FOLD - CLEAR`, full inner width except the USB-C notch.
- [ ] **Step 2: Asserts** (the script must fail loudly when any breaks):
  - `abs(T - 7.15) < 0.01`.
  - USB-C top `<=` back face: `MASK_T + PANEL_T + XIAO_GAP + XIAO_T <= INNER + BACK_WALL`.
  - Switch and backstop clear the XIAO, the USB-C notch and the cable fold by at least `CLEAR` in plan.
  - The ledge leaves room for the XIAO's wire joints where it passes over the board: `MASK_T + PANEL_T + XIAO_GAP - LEDGE_T >= 0.45 + CLEAR`; and its top edge `<= panel_y - FOLD - CLEAR` (clear of the cable fold).
  - Magnet bosses vs battery: allowed to overlap in plan only if `INNER - (MASK_T + PANEL_T + CLEAR + BATT_T) >= MAG_PROUD + CLEAR` where `MAG_PROUD = 0.4`; otherwise fail.
  - Battery top below the top wall with `CLEAR`.
- [ ] **Step 3: Draw** a front view (sheet outline, picture window, masked strip, parts behind dashed, switch, ledge, pinhole) and one side section through the XIAO, like `layout_compact.png`; title with `CASE_W x CASE_H x T`. Print the case size, chin height and %, switch position, ledge size and the boss/battery depth margin.
- [ ] **Step 4: Run it.** Run: `python3 case/layout_acrylic.py`. Expected: no assertion error; prints `case 61.0 x 94.7x x 7.15`; writes `case/layout_acrylic.png`. Look at the PNG.
- [ ] **Step 5: Checkpoint with Erik.** Show the PNG; agree the layout before CAD (skill rule). Record his answer in `docs/ledger.md` (`Task 7 (acrylic case): Ruling ...`), including the `XIAO_GAP` 0.65 ruling.
- [ ] **Step 6: Commit.** `git add case/layout_acrylic.py case/layout_acrylic.png docs/ledger.md && git commit -m "Case: acrylic-front layout (mounting A, edge button, 7.15)"`

### Task 2: Edge-button logic (PC-tested) and the plan's wiring text

**Files:**
- Modify: `firmware/magnet/settings.h`, `firmware/magnet/logic.h`, `firmware/magnet/logic.c`, `firmware/test/test_logic.c`, `docs/plan.md` (pin map, Task 5, Task 8), `docs/design.md` (Behavior), `docs/ledger.md`

**Interfaces:**
- Produces: `typedef enum { BUTTON_NEXT_PHOTO, BUTTON_SETUP } button_action_t;` and `button_action_t button_action(uint32_t held_ms);` in `logic.h`; `SETUP_HOLD_MS` (5000u) in `settings.h`.

- [ ] **Step 1: Write the failing test** `test_button_action` in `test_logic.c`, called from `main`:

```c
CHECK(button_action(0) == BUTTON_NEXT_PHOTO);            /* bump or tap */
CHECK(button_action(4999) == BUTTON_NEXT_PHOTO);
CHECK(button_action(SETUP_HOLD_MS) == BUTTON_SETUP);     /* 5000 */
CHECK(button_action(60000) == BUTTON_SETUP);             /* held long, or stuck */
```

- [ ] **Step 2: Run it to see it fail.** Run: `gcc -Wall -Wextra -Werror firmware/test/test_logic.c firmware/magnet/logic.c -o /tmp/t && /tmp/t`. Expected: compile error, `button_action` undeclared.
- [ ] **Step 3: Implement.** Add `SETUP_HOLD_MS 5000u` to `settings.h` (wrapped in `#ifndef` like the others, comment "Task 5 (Erik): hold the edge button this long for setup mode"); the enum and prototype to `logic.h` with a comment block like `boot_action`'s; `button_action` in `logic.c` (`held_ms >= SETUP_HOLD_MS`).
- [ ] **Step 4: Run it to see it pass.** Same command. Expected: the suite's success line, exit code 0.
- [ ] **Step 5: Update `docs/plan.md`.**
  - Pin map: "D5 setup button (edge switch to GND, internal pull-up; acrylic case; unwired on the other cases, where the pull-up keeps it idle)".
  - Task 5 Produces: add `button_action`.
  - Task 5 Step 3: the setup screen explains only how to join `FridgeMagnet-Setup` and open the page; how to start setup again goes on the printed card for each case type (Ruling: the screen is shared by all case types).
  - Task 5 Step 4: wake sources are the timer and EXT1 `ESP_EXT1_WAKEUP_ANY_LOW` on D5 and D9 (Task 8's MPU6050 interrupt configured active-low, `INT_PIN_CFG.INT_LEVEL = 1`). Enable D5's pull-up (`rtc_gpio_pullup_en`, `rtc_gpio_pulldown_dis`) before arming. On a D5 wake, time how long D5 stays low, up to `SETUP_HOLD_MS`, and act on `button_action`: `BUTTON_NEXT_PHOTO` runs the normal fetch and draw (not counted against the shake cap); `BUTTON_SETUP` opens the portal as on the third failure. Before sleeping, leave D5 out of the EXT1 mask while it still reads low (stuck button), so the magnet does not wake in a loop. The reset double press stays.
  - Task 5 Step 5: add bench checks: a tap shows the next photo; a 5 s hold opens setup; holding the button through sleep does not re-wake (measure current: back to the sleep figure); with D5 unwired, 24 h of timer wakes and no D5 wake.
  - Task 8 Step 4: "EXT1 wake on D9" becomes "EXT1 any-low on D9 (and D5), MPU interrupt active-low".
- [ ] **Step 6: Update `docs/design.md`** Behavior: "Setup mode: ... or, on the acrylic case, the edge button held for 5 seconds (a short press shows the next photo)." Add to `docs/ledger.md`: the `button_action` line (TDD: failed, then passed), the setup-screen ruling, and the EXT1 any-low ruling (cost if wrong: if EXT1 any-low misbehaves with two pins on the S3, D5 moves to EXT0 at a small sleep-current cost; check in Task 5 Step 5).
- [ ] **Step 7: Commit.** `git add firmware/ docs/plan.md docs/design.md docs/ledger.md && git commit -m "Firmware: edge-button hold logic (button_action, SETUP_HOLD_MS); plan wiring for D5"`

### Task 3: SolidCraft model of the acrylic case

**Files:**
- Modify: `case/solidcraft/build_case.py`
- Create (generated): `case/solidcraft/magnet_case_acrylic.json/.solidcraft/.step`, `..._acrylic_discs.*`, `tray_acrylic.stl`, `tray_acrylic_discs.stl`, `front_sheet_acrylic.stl`, `acrylic_sheet.svg`, `render_acrylic_*.png`
- Modify: `case/solidcraft/README.md`, `case/README.md`, `docs/ledger.md`, `CLAUDE.md` (Current state, one line)

**Interfaces:**
- Consumes: Task 1's agreed numbers.
- Produces: `python3 build_case.py acrylic [discs]`.

- [ ] **Step 1: Prove the old outputs are untouched first.** Run all four existing builds and `git diff --exit-code case/solidcraft/*.json`. Expected: no diff (baseline).
- [ ] **Step 2: Add the `acrylic` option** to `build_case.py`. `ARGS <= {"discs", "compact", "acrylic"}`; `ACRYLIC = "acrylic" in ARGS` implies the compact layout (`SQUARE`) and then overrides; every existing mounting-B feature is guarded `if SQUARE and not ACRYLIC`. Parameters (names exact, comments with sources):
  - `SheetT` 1 mm, `MaskT` 0.1 mm (vinyl), `XiaoGap` 0.65 mm, `SideFrame` and `TopFrame` removed: `CaseW = PanelW + 2 * (Clear + Wall)`, `CaseH = PanelY + PanelH + Clear + Wall`.
  - `InnerD` = the Task 1 formula; `ShellH = BackWall + InnerD`.
  - `PinX = XiaoX + XiaoH - BtnFromSide`, `PinY = XiaoY + BtnFromEnd` (rear).
  - `SwX` 12 mm, `SwW` 3.5, `SwD` 2.9, `SwT` 1.6, `PlungerW` 1.6, `PlungerH` 1.0 (placeholders until the switch is chosen), `LedgeT` 0.8 mm, `LedgeTop = PanelY - Fold - Clear`.
- [ ] **Step 3: Features** (one body `Tray`, one body `FrontSheet`), named:
  - `Shell`, `Hollow` (as today, `BackShell` renamed `Tray` for this type).
  - Magnets: the existing `Bosses`/`Pockets` (bars) or disc `Pockets`, right side above the XIAO as in compact.
  - `Ribs`: left rib only, full `InnerD` height (it now also carries the sheet).
  - `PinholeCut`: through the back wall at `PinX, PinY`.
  - `UsbNotchCut`: rect `UsbCX ± (UsbW / 2 + Clear)`, `y -1 mm .. UsbLen + Clear`, cut from z 0 through `ShellH` (opens the back wall and the bottom wall, as v1's notch).
  - `SwitchSlot`: plunger slot through the bottom wall at `SwX`, centred at `z = BackWall + SwT / 2`; `SwitchBackstop`: a `RibT` rib behind the switch, `SwW + 2 mm` wide, from the back wall to `BackWall + SwT`.
  - `ChinLedge`: from `z = ShellH - LedgeT` to `ShellH`, `y Wall .. LedgeTop`, joined to the walls, cut clear of the USB-C notch.
  - `FrontSheet`: the case outline (`CornerR`), `SheetT` thick, on top of the tray (`z = ShellH`), no cuts. Model only: it is laser cut, not printed.
  - Finishing: `BackEdgeFillet` (`BackR`) on the tray's back outline; `RimFillet` (0.3 mm) on the tray's top outer edge; the sheet's edges stay square. No front fillet or window chamfer.
- [ ] **Step 4: Sheet and mask outline.** In the `acrylic` build, also write `acrylic_sheet.svg` (mm units, `viewBox` = `CaseW x CaseH`): the cut outline (rounded rect, `CornerR`) as a red 0.01 mm stroke, and the mask's window (`WinX, WinY, WinW, WinH`, sheet coordinates mirrored left-right because the vinyl goes on the back) as a blue 0.01 mm stroke; a text note "vinyl on the back; window mirrored".
- [ ] **Step 5: Build.** From `case/solidcraft`: `python3 build_case.py acrylic` then `$CLI run magnet_case_acrylic.json --save magnet_case_acrylic.solidcraft --out magnet_case_acrylic.step --results --quiet --json-out /tmp/res.json`; same for `acrylic discs`. Expected: both runs exit 0.
- [ ] **Step 6: Verify** with the skill's checker: `python3 $SKILL/scripts/verify.py --cli "$CLI" --design magnet_case_acrylic.solidcraft --out /tmp/acr --change XiaoGap="1 mm" --change CornerR="5 mm" --change SwX="15 mm" --change LedgeT="0.6 mm"` (and the discs design with `--change XiaoGap="1 mm" --change CornerR="5 mm"`). Expected: exit 0, 0 interferences, every feature rebuilt, face counts unchanged. Copy the STLs to `tray_acrylic(_discs).stl` and `front_sheet_acrylic.stl`; take `render_acrylic_front.png`, `_back.png`, `_inside.png` (sheet hidden) with `$CLI snapshot`, and look at them: rear pinhole over the XIAO button, notch flush, switch slot in the bottom wall, ledge under the sheet, no slivers under 0.8 mm between cut-outs.
- [ ] **Step 7: Old outputs still identical.** Regenerate the four existing JSONs; `git diff --exit-code case/solidcraft/*.json` (excluding the new acrylic files). Expected: no diff.
- [ ] **Step 8: Docs.** `case/solidcraft/README.md`: a new section "Acrylic-front version" (size, mounting A, sheet and SVG, switch placeholders, what was checked, what is unmeasured, assembly: VHB on rim, ribs and ledge; vinyl on the back of the sheet; foam behind the panel; the 0.4 skin is two FDM layers, print a test patch). `case/README.md`: one paragraph pointing to it. `CLAUDE.md` Current state: add the acrylic case as an additional case type. `docs/ledger.md`: the build and verify result.
- [ ] **Step 9: Commit.** `git add case/ docs/ledger.md CLAUDE.md && git commit -m "Case: acrylic-front case type (tray + sheet, mounting A, edge button) in SolidCraft"`
