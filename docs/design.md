# E-ink Polaroid Fridge Magnet: Design and Off-the-Shelf BOM

Status: approved by Erik. Phase 2 (custom PCB) is out of scope here; see `phase2-custom-pcb.md`.

## Intent
A gift for Erik's parents: a thin color e-ink photo magnet for the fridge. It should feel more like a magnet than a digital picture frame. Erik uploads photos from anywhere over the internet; the magnet wakes once a day, shows the next photo, and goes back to sleep. Inspired by VidaBay Snap (which uses NFC and no battery; Erik wants Wi-Fi).

## Goals
- As thin as possible (Polaroid-like look, printed case with a white chin; the top case may mask the panel edges to frame the photo, an idea to be tried).
- Color e-ink (Spectra 6), 3.7 inch, 480x720 portrait.
- Months per charge; the photo stays on screen with no power.
- Parents can set up Wi-Fi themselves through a setup mode.
- Secure uploads over the internet (only Erik can upload).
- Off-the-shelf parts only, no custom PCB in this phase.

## Non-goals
- Parents uploading photos, video, touch, or buttons for browsing.
- Always-on display or fast refresh.

## Anti-goals (failure even if it works)
- Feels like a bulky gadget or a tablet.
- Dies silently with an old photo and parents don't know why.
- Photos exposed publicly or reachable without auth.

## Approaches considered
1. Display driver board with panel plugged in: least wiring, bulkier, higher sleep current.
2. **Chosen:** separate low-power ESP32 board plus panel adapter plus thin LiPo. Best battery life and thinnest case; needs some wiring.
3. M5Stack PaperColor in a custom case: simplest but too bulky.
Also rejected: Waveshare 15823 universal driver board (no charger, E6 support not stated), nRF boards (mostly no Wi-Fi; sleep current is not the dominant cost).

## Off-the-shelf BOM
| # | Part | Key specs | Notes |
|---|------|-----------|-------|
| 1 | Good Display GDEH037E01, 3.7" Spectra 6 panel (480x720, portrait) | Active area 50.4x75.6 mm in the datasheet table but 51.6x77.04 mm on its drawing (measure; see `case-dimensions.md`), outline 58x85.64 mm, about 0.85 to 0.9 mm thick, 32-pin 0.8 mm FPC, 26 mm wide. Datasheet power and refresh time are TBD; the product page lists deep sleep under 10 uA (typ.) | Controller is IST7601 on the datasheet drawing but JD7601 in Good Display's sample code. Datasheet says avoid acetic-acid and chlorine-type materials near the panel (use neutral-cure adhesive), use a protective cover plate, avoid twisting. Fallbacks: GDEP040E01 4" or Waveshare 3.6"/4" (600x400) |
| 2 | Panel adapter, Good Display DESPI-E01 (for 1.54" and 3.7" Spectra 6) | 35.185x20.647 mm, 3.3 V, 8-pin header: BUSY, RES, DC, CS, SCL, SDA, GND, 3V3 | Confirm with the seller that its FPC connector fits the panel's 32 pins (the adapter FAQ says 24-pin) and check its thickness |
| 3 | Seeed XIAO ESP32-S3 (plain, not the Sense variant) | Deep sleep about 14 uA, 110 mA battery charging (v1.4 schematic; the wiki says 50 mA), onboard USB-C, external U.FL rod antenna | Battery attaches to solder pads |
| 4 | Thin LiPo, 3.7 V, 300 to 500 mAh (candidates: 303450, DNK 252548) | 303450: 500 mAh, 3.0 x 34 x 50 mm (Erik), protection circuit, max charge 0.5C (250 mA). DNK 252548: capacity, thickness and protection unconfirmed | Direct-soldered to the XIAO battery pads (JST cut off); check polarity against the XIAO silkscreen and insulate the joints. Erik ordered the 303450 |
| 5 | Battery-sense divider: 2x 1 MOhm resistors plus small capacitor | Reads battery voltage on an ADC pin | No fuel gauge on this board |
| 6 | Neodymium bars, 8 x 3 x 1 mm, 12 of them | Glued into pockets in the back wall, six along each side | Hold strength to be tested. Erik chose neodymium (a magnetic sheet and 8x1 discs were considered) |
| 7 | Printed case (Erik prints) | White chin holds board and USB-C, battery behind panel | USB-C opening cut so the case wraps the connector face and leaves it exposed, which should save about 1.5 to 2 mm (Erik's estimate); overall thickness not measured |
| 8 | Hookup wire, Kapton tape, double-sided adhesive | | |
| 9 | MPU6050 breakout (for the optional shake feature, Task 8) | Motion interrupt pin | Breakout LED and regulator draw milliamps: remove them before measuring sleep current |

Erik has ordered: XIAO ESP32-S3, the GDEH037E01 panel with its driver adapter, a 303450 battery, and an MPU6050.

## Behavior
- Wake on a timer once a day (Erik's call), join Wi-Fi, fetch the next ready-to-display image, draw it, report battery, sleep.
- Optional extra: shake the magnet to show the next photo (max 8 a day).
- Setup mode: if Wi-Fi fails repeatedly, or the reset button is pressed twice within 5 seconds (a paperclip through a pinhole in the back; one press just shows a fresh photo), or, on the acrylic case, the edge button is held for 5 seconds (a short press shows the next photo), the magnet creates its own hotspot and a phone page lets parents choose their Wi-Fi.
- Low battery: draw a small battery icon, and report battery to the server so Erik gets a notice.

## Web app and security
- Erik logs in and uploads photos; the server resizes and dithers each photo to the 6 panel colors at 480x720 portrait, packed at 4 bits per pixel (172,800 bytes per frame).
- The device only downloads a ready bitmap over HTTPS with a per-device token. No inbound connections to the device.
- Hosting (my call): a small web app on Erik's own server or a cheap cloud host, behind a TLS reverse proxy.

## Battery estimate (assumptions, not measured)
About 1 wake a day at roughly 30 s and 80 mA is about 0.7 mAh/day; sleep at roughly 20 uA is about 0.5 mAh/day; self-discharge adds about 0.4 to 1 mAh/day. That is roughly 2 to 3 months on 150 mAh and 4 to 5 months on 400 mAh. Each extra shake refresh costs about as much as the daily one (about 0.7 mAh, unmeasured). Measure real wake current on a prototype.

## Verify before ordering / building
- Panel FPC and adapter compatibility (panel lists 32 pins, adapter FAQ says 24), and adapter thickness.
- Battery polarity against the XIAO battery pads (direct solder), and the DNK 252548 datasheet.
- Real wake current, refresh time and refresh current (TBD in the datasheet), and sleep current.
- Magnet strength through the case.

Good Display's ESP32 sample code (not run) shows the panel sequence: write the frame (command 0x10), power on (0x04), refresh (0x12), power off (0x02), then deep sleep (0x07). Waking from panel deep sleep needs a hardware reset. The sample sends one byte per SPI transfer at 2 MHz, which is likely slow; batch it. Its pins are for a generic ESP32-S3 board and need remapping for the XIAO.

## Phase 2: custom PCB (later)
See `phase2-custom-pcb.md`.
