# Phase 2 notes: custom PCB (exploration, "just for fun")

Goal (Erik): get more into custom PCB design and build a few to give away. Parked until the off-the-shelf build is measured.

## Decisions so far
- 4-pin magnetic pogo pins (power plus USB data) replace the USB-C connector. Reverse-polarity protection on the charge input; key the magnet polarity so it seats one way. Test pads as a flashing backup.
- Case: printed or a PCB sandwich (FR4 back plate and front bezel, white soldermask chin). Keep copper off the antenna edge. A metal case was considered and dropped (blocks Wi-Fi, annoying to deal with).
- Load switch cutting power to the panel supply and the battery-sense divider between wakes. Hold the panel control lines low or high-impedance while it is off so they do not back-feed.
- Shake-to-refresh with an accelerometer wake-on-motion interrupt, capped at 8 a day, in addition to the daily update. Deliberate-shake pattern so a fridge door does not trigger it.
- Magnets: Erik will use neodymium discs.

## Ideas not yet decided
- Bare ESP32-S3 module (firmware carries over) versus ESP32-C6 (may sleep lower, needs a port). Check whether the 172,800-byte frame fits internal RAM or needs PSRAM.
- Fuel gauge IC instead of the divider (check its own sleep current).
- Capacitive touch pad instead of a mechanical setup button.
- NFC tag for Wi-Fi setup by tapping a phone (needs a flat antenna, so a non-metal case).
- Temperature sensor (e-ink refresh settings depend on temperature; verify in the panel datasheet).
- Riskiest part: the panel's boost and driver circuit, which the DESPI-E01 adapter provides today. Would be copied from Good Display's reference design (not yet seen).
- Without USB, firmware updates need OTA over Wi-Fi with a signed update path on the server.
