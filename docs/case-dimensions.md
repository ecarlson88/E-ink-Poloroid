# Case design: part dimensions

Collected for Task 7. All numbers come from the manufacturers' files in `docs/datasheets/`; none are measured yet. Measure each part with calipers when it arrives (Task 7 Step 1) and correct this file. Units: mm.

## 1. Panel: Good Display GDEH037E01 (`GDEH037E01.pdf`, p.5 table and p.6 drawing)

| Item | Value | Source |
|---|---|---|
| Outline (W x H) | **58 ±0.1 x 85.64 ±0.1** | drawing and table agree |
| Thickness | **0.85 ±0.15** without protective film (drawing); 0.9 without masking film (table) | the two disagree slightly: design for 1.0 |
| Active area (visible pixels) | **51.6 x 77.04** (drawing, pixel 0.1075 x 0.1070) vs **50.40 x 75.60** (table, pixel 0.105 x 0.105) | **the datasheet contradicts itself**: settle by measuring the lit area of a test image |
| Border (inked frame around the active area) | 52.6 x 78.04 | drawing |
| Margins, panel edge to active area (drawing) | left 3.2, right 3.2, top 2.55, bottom (FPC side) ~6.05 | top and right are dimensioned; left and bottom are derived from the outline |
| Margins, panel edge to border | left 2.7, right 2.7, top 2.05, bottom ~5.55 | same |
| Weight | 8.5 ±0.5 g | table |

The window is off-centre: the bottom (FPC) margin is about 3.5 mm wider than the top.

**Flex cable (FPC):** leaves the bottom edge, centred. About 20.3 wide where it leaves the panel (18.872 from each side), widening to **26 ±0.1** at the contacts. It reaches **20 ±0.3** beyond the panel edge, is 0.12 ±0.03 thick, and has a 2.4 ±0.2 stiffener at the end. **32 contacts at 0.8 pitch** (24.8 ±0.05 across, contact length 2.1 ±0.2). Bend area is marked near the panel edge. Do not twist it; fold it back behind the panel.

Handling notes from the datasheet: the edge seal (RTV) runs along the bottom edge, so don't glue over it ("EC glue & RTV, do not over PS"). Avoid acetic-acid and chlorine adhesives near the panel (see `design.md`).

## 2. Adapter: Good Display DESPI-E01 (`DESPI-E01.pdf`)

| Item | Value | Source |
|---|---|---|
| Board | **35.185 x 20.647** | p.4 table |
| Thickness | **not stated** | measure |
| Signal header | 8 pins, 2.54 pitch, straight male pins sticking out of one short edge, parallel to the board (BUSY, RES, DC, CS, SCLK, SDI, GND, 3V3) | p.5 photo |
| Panel connector | FPC connector along the opposite short edge (the 20.6 mm side) | p.5 photo |
| Supply | 3.3 V | p.4 table |

**FPC fit is still unconfirmed, and the datasheet makes it look worse.** Its only photo shows the adapter with the 1.54" panel, with "24" printed by the connector, and the FAQ says to use a 24-pin 0.5 mm connector. Our panel's cable is **32 pins at 0.8 mm, 26 mm wide**, and the adapter's connector edge is only 20.6 mm long. Confirm with the seller, or try the panel in the connector, before designing the chin around this board (plan Task 1 Step 1).

The header and its plastic strip (about 2.5 thick) are likely the thickest part of the adapter. Desoldering the header and soldering wires straight to the pads would save that height. This decision is open.

## 3. Controller: Seeed XIAO ESP32-S3, plain (`xiao-esp32s3/`)

| Item | Value | Source |
|---|---|---|
| Board | **21 x 17.8** (model: 20.96 x 17.78), rounded corners | Seeed wiki and product sheet, STEP model |
| Total height | **~4.5** from the underside to the top of the USB-C connector | measured from Seeed's STEP model (`XIAO-ESP32S3_v2.step`) |
| PCB + metal shield can | ~3.25 | STEP model |
| USB-C connector | on a short edge, about 8.9 wide x 4.2 tall, **sticks out ~1.5 past the board edge** | STEP model, `top_view.jpg` |
| Buttons | **R** (reset) and **B** (boot), tiny side-by-side buttons on the top face, either side of the USB-C | `top_view.jpg` |
| LEDs | orange user LED and red charge LED next to the buttons | wiki, `top_view.jpg` |
| Antenna | **external rod antenna** on a U.FL socket in the corner opposite the USB-C, top side; antenna included; its size is not stated | wiki, product page, `top_view.jpg` |
| Battery pads | **underside**, near the middle of one long edge: "BAT +/−", **− nearer the USB end** | `underside_pads.png` (from the DXF), wiki text |
| Underside | flat apart from pads ("no components on the back") | product page |
| Charge current | **110 mA** per the v1.4 schematic (ICharge = 24000/220K); wiki and product page say 50 mA | `XIAO_ESP32S3_v1.4_schematic.pdf` |
| Deep sleep | 14 uA | wiki |

## 4. Battery: 303450 LiPo

Erik is measuring. Design notes say about 33.8 x 50 x 2.7, 500 mAh, protection circuit, 0.5C max charge.

## Things that will shape the case

1. **Antenna against a steel fridge door.** The magnet sits flat on steel, which blocks and detunes a 2.4 GHz antenna behind it. Put the antenna at the front or top edge, away from the back, and check Wi-Fi signal strength on the real fridge early.
2. **Thickness budget (unmeasured):** panel ~1.0 + battery ~2.7 behind it ≈ 3.7 plus walls. The XIAO (~4.5) and the adapter (unknown, header ~2.5) are the thickest parts, which suggests putting them in the chin beside the panel rather than behind it.
3. **Chin below the panel:** the panel's wider bottom margin, the FPC exit and the chin all fall at the same edge. The FPC folds back behind the panel, so the adapter sits behind the bottom part of the panel or inside the chin.
4. **USB-C** must face an outside edge of the chin (the plan says the case wraps the connector face). Reset and boot buttons sit right beside it.
5. **Button for setup mode** (plan: D5) is a separate part not yet chosen.
