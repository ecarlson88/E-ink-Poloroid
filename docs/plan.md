# E-ink Fridge Magnet Build and Test Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans if available, otherwise work task by task in order. Steps use `- [ ]` checkboxes. Follow TDD where the plan says tests.

**Goal:** a thin color e-ink fridge magnet that wakes once a day, downloads the next photo over HTTPS, draws it and sleeps for months.

**Architecture:** a web app (Erik uploads) renders each photo to a ready 480x720 frame. A XIAO ESP32-S3 wakes on a timer, joins Wi-Fi, fetches the frame with a per-device token, sends it to the panel through the DESPI-E01 adapter, reports battery and deep-sleeps.

**Tech stack:** Python 3 with FastAPI, Pillow and SQLite for the server, in Docker behind a TLS reverse proxy; the firmware is an Arduino IDE sketch (Erik's choice: Arduino-ESP32 core, board "XIAO_ESP32S3"), ported from Good Display's ESP-IDF sample (`firmware/reference/GDEH037E01_idf.c`). Pure logic is plain C in the sketch folder (`logic.c`) so it is tested on the PC with `gcc`. Settings that were `menuconfig`/Kconfig values live in `firmware/magnet/settings.h` (committed) and `firmware/magnet/secrets.h` (git-ignored; template `secrets.example.h`).

**Spec:** `docs/design.md`.

**Status:** Tasks 2 and 3 are built in `server/` (Task 3 Step 5, the HTTPS deploy check, is pending). The PC-tested logic is done: Task 4 Steps 1 to 3, Task 5 Steps 1 and 2, Task 6 Steps 1 and 2, Task 8 Steps 1 and 2. Tasks 1 and 4 to 8 need the hardware, which Erik has ordered. See `docs/ledger.md`.

## Global constraints

- Panel: Good Display GDEH037E01, 480x720 portrait, Spectra 6, 4 bits per pixel, 172,800 bytes per frame.
- Palette nibble values from Good Display's sample: black 0, white 1, yellow 2, red 3, blue 5, green 6.
- Panel sequence: write frame (0x10), power on (0x04), refresh (0x12), power off (0x02), deep sleep (0x07 with 0xA5). Waking panel deep sleep needs a hardware reset.
- MCU: plain Seeed XIAO ESP32-S3. Battery 3.7 V LiPo, 300 to 500 mAh, direct-soldered.
- One wake a day. Device makes outbound HTTPS only, with a per-device bearer token. Only Erik can upload.
- Photos never served without auth. No inbound connections to the device.
- Pin map is a call from memory, to check against Seeed's XIAO ESP32-S3 pinout before wiring: MOSI D10, SCK D8, CS D1, DC D2, RST D3, BUSY D4, battery sense D0, setup button D5, MPU6050 SDA D6, SCL D7, INT D9 (a deep-sleep-capable pin).
- Low battery threshold is a call: 3.5 V.

## Review focus

Inputs the spec implies but never states. Each has a test in the task named.

1. Phone photos with EXIF rotation or odd aspect ratios come out upright and fill the frame (Task 2).
2. Oversized or non-image uploads (HEIC, 40 MB, a renamed text file) are rejected with a clear error and nothing is stored (Task 3).
3. A truncated, empty or non-200 download never triggers a panel refresh; the old photo stays and the device sleeps (Task 4).
4. After a router or password change, repeated Wi-Fi failures lead to a setup screen the parents can act on, not a silently dead magnet (Task 5).
5. A low battery reading caused only by Wi-Fi radio current sag does not trigger a false alert: the battery is read before Wi-Fi starts, and the server alerts only after two low reports in a row (Tasks 3 and 6).

---

### Task 1: Bench bring-up and measurements

Proves the panel, adapter and wiring, and replaces the TBD numbers in the datasheet with real ones. Nothing else on the device is built until this passes.

**Files:** create `firmware/bench/bench.ino` (Arduino port of Good Display's `GDEH037E01_idf.c`, pins remapped); create `firmware/bench/RESULTS.md`.

**Produces:** `RESULTS.md` with panel refresh time, refresh and sleep currents, byte/nibble order and orientation. Tasks 2, 4 and 6 read these.

- [ ] **Step 1: Confirm the FPC fit.** Before wiring, ask the seller whether the DESPI-E01's connector fits the GDEH037E01's 32-pin FPC. Pass: written yes, or the panel seats in the connector.
- [ ] **Step 2: Wire the XIAO to the adapter** using the pin map in Global constraints (3V3, GND, BUSY, RES, DC, CS, SCL, SDA). Pass: no shorts; the XIAO enumerates over USB.
- [ ] **Step 3: Port `bench.ino`** using the XIAO pin names and keep the sample's init and refresh sequence. Build in the Arduino IDE and flash. Pass: the sample image appears on the panel.
- [ ] **Step 4: Settle the frame layout.** Draw a test frame with a distinct color in each corner and a different color for the first pixel of the first row. Record in `RESULTS.md`: which nibble is the left pixel, which corner is the origin, and whether portrait is right-way-up with the adapter at the bottom. (If different from the assumptions in `server/imaging.py`, flip `HIGH_NIBBLE_IS_LEFT` or the orientation there.)
- [ ] **Step 5: Batch the SPI writes.** Change the byte-at-a-time data write to one DMA transfer of at least 4,096 bytes at 10 MHz or the panel's stated limit. Pass: the same image still draws, and the data transfer time is logged.
- [ ] **Step 6: Measure.** In `RESULTS.md` record: full refresh time (log the time from command 0x12 to BUSY release), supply current during refresh and after power off, panel deep-sleep current, and XIAO deep-sleep current with the panel in deep sleep. State the instrument used.
- [ ] **Step 7: Check the wake path.** Put the panel into deep sleep, hardware-reset it, run the init and draw again. Pass: the second draw succeeds with no stuck BUSY.

### Task 2: Server image pipeline (DONE, `server/imaging.py`)

Turns any photo into the exact frame the panel takes.

**Files:** `server/imaging.py`; test `server/tests/test_imaging.py`; `server/pyproject.toml`.

**Consumes:** nibble order and orientation from Task 1's `RESULTS.md` (currently assumed: left pixel is the high nibble, rows run top to bottom).

**Produces:** `render_frame(photo: bytes) -> bytes` (exactly 172,800 bytes; raises `ValueError` for non-images or more than 50 million pixels) and `PALETTE: dict[int, tuple[int, int, int]]` keyed by nibble value 0, 1, 2, 3, 5, 6.

Remaining follow-up: PALETTE RGB values are nominal pure colors and are tuned in Task 4 Step 6.

### Task 3: Server API, auth and alerts (DONE except Step 5)

**Files:** `server/app.py`, `server/notify.py`, `server/static/index.html`; test `server/tests/test_api.py`.

**Consumes:** `render_frame` from Task 2.

**Produces (the contract Task 4 calls):**

- `GET /api/device/next?bat_mv=<int>` with `Authorization: Bearer <DEVICE_TOKEN>` returns `200 application/octet-stream`, a 172,800-byte frame, and header `X-Photo-Id`. It returns `204` when no photos exist and `401` for a missing or wrong token. Each call takes the next photo from a shuffle (each photo once per round, never the same twice in a row; Erik can pick the next one on the page).
- `POST /login` (form field `password`, checked against env `UPLOAD_PASSWORD_HASH`) sets a session cookie. `POST /api/photos` (multipart `file`), `GET /api/photos` and `DELETE /api/photos/{id}` require that cookie and return `401` without it.
- `notify_low_battery(battery_mv: int) -> None` in `notify.py` posts JSON `{"battery_mv": n}` to env `LOW_BATTERY_WEBHOOK_URL`.
- Config comes from env: `DEVICE_TOKEN`, `UPLOAD_PASSWORD_HASH`, `SESSION_SECRET`, `LOW_BATTERY_WEBHOOK_URL`, `DATA_DIR`.

- [ ] **Step 5: Deploy and verify over HTTPS.** Run uvicorn (`uvicorn app:create_app --factory`) under systemd behind a TLS reverse proxy. Pass: `curl -i https://<host>/api/device/next` returns `401`; the same call with the token returns `200` and 172,800 bytes (`curl -s ... | wc -c`); plain HTTP is refused or redirected.
- [ ] **Follow-up (deferred minor):** throttle failed logins on `/login`.

### Task 4: Firmware core loop

Wake, join Wi-Fi, fetch, draw, sleep. Pure decisions live in `logic.c` so they can be tested on the PC; everything else is checked on the bench.

**Files:** create `firmware/magnet/magnet.ino`, `epd.cpp`/`epd.h` (from Task 1's `bench.ino`), `net.cpp`/`net.h`, `logic.c`/`logic.h`, `settings.h` (`FAIL_RETRY_SECONDS` default 3600), `secrets.example.h` (`SERVER_URL`, `DEVICE_TOKEN`, dev-default `WIFI_SSID`/`WIFI_PASS`); test `firmware/test/test_logic.c` (plain C, built with `gcc`).

**Consumes:** Task 3's `GET /api/device/next` contract; Task 1's pin map, nibble order and orientation.

**Produces:**

- `bool frame_ok(int http_status, size_t len)` and `uint32_t next_sleep_seconds(bool success, int consecutive_failures)` in `logic.h`.
- `bool epd_show_frame(const uint8_t *frame, size_t len)` in `epd.h`: returns `false` and leaves the panel untouched unless `len == 172800`; otherwise runs reset, init, write, power on, refresh, power off, panel deep sleep.
- `bool wifi_join(const char *ssid, const char *pass, uint32_t timeout_ms)` and `bool net_fetch_frame(uint8_t *buf, size_t cap, size_t *out_len, int bat_mv, int *http_status)` in `net.h` (Arduino port: `bool` instead of `esp_err_t`). Fetch uses HTTPS (`WiFiClientSecure` with the certificate bundle) and the bearer token; the buffer is allocated from PSRAM (check whether internal RAM suffices).
- A consecutive-failure counter kept in NVS through `Preferences` (`wake_fail`).

- [x] **Step 1: Write the failing tests** in `test_logic.c`: `frame_ok(200, 172800) == true`; `false` for `(200, 172799)`, `(200, 0)`, `(204, 0)`, `(401, 172800)`, `(500, 172800)`. `next_sleep_seconds(true, 0) == 86400`; `next_sleep_seconds(false, 1) == FAIL_RETRY_SECONDS`.
- [x] **Step 2: Run `gcc firmware/test/test_logic.c firmware/magnet/logic.c -o /tmp/t && /tmp/t`.** Expected: FAIL to build.
- [x] **Step 3: Implement `logic.c`.** Run again. Expected: PASS.
- [ ] **Step 4: Implement `epd.cpp`, `net.cpp` and `magnet.ino`.** Flow: read battery (stub returning 4000 until Task 6), join Wi-Fi (20 s timeout, 2 tries), fetch, check `frame_ok`, `epd_show_frame`, reset `wake_fail` to 0 on success, else increment it; then `esp_deep_sleep` (callable from Arduino) for `next_sleep_seconds(...)`.
- [ ] **Step 5: Verify on the bench against the deployed server.** Pass: serial log shows the photo id and the photo appears; the device then sleeps. With a wrong token in `secrets.h`, the log shows `keeping old image`, the panel does not refresh, and the next wake is scheduled for `FAIL_RETRY_SECONDS`.
- [ ] **Step 6: Tune colors.** Show a six-color swatch frame from the server, photograph it next to the panel in daylight and adjust `PALETTE` RGB values in `server/imaging.py` until skin tones and grass look right. Commit the final values.
- [ ] **Step 7: Measure the awake time and the supply current for one full wake** and enter both in `RESULTS.md`, with a revised battery-life estimate.
- [ ] **Step 8: Commit.**

### Task 5: Setup mode

Lets the parents join their own Wi-Fi, and tells them how when the magnet cannot connect.

**Files:** create `firmware/magnet/setup_portal.cpp`/`.h` (Arduino `WebServer` and `DNSServer`), `firmware/magnet/setup_screen.h` (generated), `tools/make_setup_screen.py`; modify `logic.c`, `magnet.ino`; extend `test_logic.c`.

**Consumes:** `wake_fail` counter and `epd_show_frame` from Task 4.

**Produces:** `bool should_enter_setup(int consecutive_failures)` (true at 3 or more); `bool setup_portal_run(uint32_t timeout_s)` (starts the open hotspot `FridgeMagnet-Setup`, a catch-all DNS and an HTTP page that lists nearby networks and accepts SSID and password; saves them to NVS namespace `wifi`; returns `true` once the device has joined that network); `setup_screen_frame[172800]`, a prerendered frame reading how to connect.

- [x] **Step 1: Write the failing tests:** `should_enter_setup(2) == false`, `should_enter_setup(3) == true`, `should_enter_setup(10) == true`.
- [x] **Step 2: Run the host test.** Expected: FAIL. Implement `should_enter_setup`. Expected: PASS.
- [ ] **Step 3: Generate `setup_screen.h`.** `make_setup_screen.py` draws large text with Pillow (network name `FridgeMagnet-Setup`, "hold the button 3 seconds", "then open the page that appears on your phone") and writes the packed frame through `render_frame`. Pass: the header has exactly 172,800 bytes of data.
- [ ] **Step 4: Implement `setup_portal_run` and wire `magnet.ino`.** On the third consecutive failed wake, draw `setup_screen_frame`, open the portal for 10 minutes, then sleep 24 hours. A press of the setup button (GPIO wake, D5) held for 2 seconds opens the portal the same way. (The button is also a deep-sleep wake source: a call.) **Changed (Erik): no separate button; a rear pinhole reaches one of the XIAO's own buttons. Pending Erik's choice: reset pressed twice within a few seconds (recommended), or boot (GPIO0, an RTC pin, but a strapping pin: must not be held through a reset). D5 is then free.**
- [ ] **Step 5: Verify on the bench.** Put a wrong password in NVS and set `FAIL_RETRY_SECONDS` to 30. Pass: after three failed wakes the screen shows the setup instructions; a phone joins `FridgeMagnet-Setup`, submits the right credentials, and the next wake fetches a photo. Repeat with the button instead of failures.
- [ ] **Step 6: Commit.**

### Task 6: Battery reading and low-battery cue

**Files:** create `firmware/magnet/battery.cpp`/`.h`; modify `logic.c`, `magnet.ino`; extend `test_logic.c`.

**Produces:** `int battery_read_mv(void)` (16 ADC samples averaged with `analogReadMilliVolts`, which applies the factory calibration, divider ratio 2, read on D0); `bool battery_low(int mv)` (true below 3500); `void overlay_low_battery(uint8_t *frame)` (stamps a 48x24 battery icon, packed in the frame's nibble format, in the top-right corner, 16 px from each edge).

- [x] **Step 1: Write the failing tests:** `battery_low(3499) == true`, `battery_low(3500) == false`; with a frame of all `0x11`, `overlay_low_battery` changes bytes only inside the icon rectangle and leaves every other byte `0x11`; calling it twice gives the same frame.
- [x] **Step 2: Run the host test.** Expected: FAIL. Implement. Expected: PASS.
- [ ] **Step 3: Read the battery before Wi-Fi starts** in `magnet.ino` and pass it to `net_fetch_frame`; if `battery_low`, call `overlay_low_battery` on the frame before `epd_show_frame`.
- [ ] **Step 4: Calibrate.** With a multimeter on the battery, compare at three charge levels and record the offset in `RESULTS.md`. Also read once after Wi-Fi connects and record the sag. Pass: the pre-Wi-Fi reading is within 50 mV of the meter.
- [ ] **Step 5: Verify the alert end to end.** Feed `bat_mv=3400` through two bench wakes. Pass: the screen shows the icon and the webhook delivers one alert.
- [ ] **Step 6: Commit.**

### Task 7: Case, magnets and assembly

**Files:** create `case/` (CAD source and exported STL for the front frame and back shell, in the CAD tool Erik prefers); append measurements to `firmware/bench/RESULTS.md`.

**Consumes:** a working bench build from Tasks 1 to 6.

**Produces:** the finished magnet and a measured total thickness.

- [ ] **Step 1: Measure the dry stack** with calipers: panel, adapter, XIAO, battery (303450 first; the DNK 252548 only once its datasheet is confirmed) laid in their intended positions. Record each thickness and the total.
- [ ] **Step 2: Design the case around those numbers.** Front frame window sized to the panel's measured active area (the datasheet says both 50.4x75.6 and 51.6x77.04; see `docs/case-dimensions.md`), with the frame covering the panel edge (the masking idea); white chin behind which the XIAO and adapter sit; USB-C opening cut so the case wraps the connector face; button access; magnet pockets on the back shell. Pass: the dimensions in the CAD file match Step 1 with at least 0.2 mm clearance, and the USB-C cable plugs in fully.
- [ ] **Step 3: Print a test shell** and dry-fit the electronics with no adhesive. Pass: nothing presses on the panel face, the battery has room, the button works. Revise and reprint until it does. Record the final overall thickness.
- [ ] **Step 4: Assemble.** Use neutral-cure adhesive and double-sided tape near the panel (no acetic-acid or chlorine types), insulate the battery solder joints with Kapton, keep the FPC free of twist, and leave the battery unpunctured and unpinched.
- [ ] **Step 5: Magnet test.** Glue in the neodymium magnets (strength to be tested). Pass: it holds on the real fridge door and stays put through 20 door open and close cycles. If it slides, add magnets or a grippier back layer. (Also check that the parents' fridge door is magnetic: stainless can be non-magnetic.)
- [ ] **Step 6: Run the real schedule for two weeks** with the server's `last_seen` and `battery_mv` logged each day. Pass: 14 daily updates, a different photo each day, and a battery drop consistent with the revised estimate from Task 4 Step 7. Then hand it over with the setup instructions for the parents on one printed card.
- [ ] **Step 7: Commit** the case files.

### Task 8: Shake to refresh (optional)

An extra photo change on top of the daily one, woken by an MPU6050 motion interrupt. Capped at 8 a day.

**Files:** create `firmware/magnet/shake.cpp`/`.h` and `firmware/magnet/mpu6050.cpp`/`.h` (Arduino `Wire`); modify `logic.c`, `magnet.ino`; extend `test_logic.c`.

**Consumes:** the fetch and draw path from Task 4; `RESULTS.md` from Tasks 1 and 4.

**Produces:**

- `bool shake_is_deliberate(const int16_t *dev_mg, size_t n, int16_t threshold_mg, int min_peaks)`: `dev_mg` is the absolute difference between acceleration magnitude and 1,000 mg, sampled at 100 Hz. A peak is a rising crossing of `threshold_mg` with at least 8 samples (80 ms) since the previous peak. Returns true when peaks >= `min_peaks`. Defaults, to be tuned: 1,500 mg and 4 peaks over 150 samples.
- `bool shake_allowed(int shakes_today, uint32_t seconds_since_last, int cap, uint32_t min_gap_s)`: true when `shakes_today < cap` and `seconds_since_last >= min_gap_s`. Defaults: cap 8, gap 300 s.
- `uint32_t remaining_sleep_seconds(uint64_t deadline_us, uint64_t now_us)`: 0 if the deadline has passed. A shake must not move the daily wake.
- `bool mpu6050_init_motion_wake(void)` (I2C on D6/D7, motion interrupt latched on D9) and `bool mpu6050_read_dev_mg(int16_t *out)`.
- In RTC memory: `shakes_today` (reset on every daily timer wake), `last_shake_us` and `next_daily_deadline_us`.

- [x] **Step 1: Write the failing tests:** `shake_is_deliberate`: 150 samples of 50 mg noise gives false; one 4,000 mg spike (a door slam) gives false; four 2,000 mg peaks 20 samples apart gives true; four peaks 3 samples apart count as one and give false. `shake_allowed(7, 600, 8, 300) == true`, `(8, 600, 8, 300) == false`, `(2, 100, 8, 300) == false`. `remaining_sleep_seconds(100000000, 40000000) == 60`; with `now_us` past the deadline it returns 0.
- [x] **Step 2: Run the host test.** Expected: FAIL. Implement the three functions in `logic.c`. Expected: PASS.
- [ ] **Step 3: Bring up the MPU6050.** Read `WHO_AM_I` and log it (typical value 0x68; clone parts can differ, so log and do not hard-fail). Implement `mpu6050.c`. Pass: shaking the board toggles the interrupt pin and `mpu6050_read_dev_mg` returns values near 0 at rest.
- [ ] **Step 4: Wire up wake and the flow in `magnet.ino`.** Enable EXT1 wake on D9. On a shake wake: sample 150 readings at 100 Hz; if not deliberate or not allowed, clear the MPU interrupt and re-sleep without touching Wi-Fi or the panel; otherwise run the Task 4 fetch and draw, increment `shakes_today` and set `last_shake_us`. Always re-arm the timer with `remaining_sleep_seconds(next_daily_deadline_us, now)`.
- [ ] **Step 5: Tune on the bench.** Do 10 deliberate shakes, 10 hard table knocks, and 10 slams of the real fridge door with the magnet attached. Pass: at least 9 of 10 deliberate shakes change the photo and none of the knocks or slams do. Adjust `threshold_mg` and `min_peaks` and record the final values.
- [ ] **Step 6: Verify the cap.** With the gap set to 0 in `settings.h`, shake 9 times. Pass: the 9th is ignored, and the count resets after the next daily timer wake.
- [ ] **Step 7: Measure sleep current with the MPU in motion-wake mode.** Remove the breakout's LED and regulator, or use a bare chip, and record the figure in `RESULTS.md`. Recompute the battery estimate for 0, 2 and 8 shakes a day. Erik decides whether the cost is acceptable.
- [ ] **Step 8: Commit.**
