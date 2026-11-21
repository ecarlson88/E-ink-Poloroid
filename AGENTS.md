# E-ink fridge magnet: handoff for a coding agent

Erik is building a thin color e-ink photo fridge magnet as a gift for his parents. He uploads photos through a web app; a battery-powered ESP32 wakes once a day, fetches the next photo over HTTPS, draws it on a Spectra 6 panel and deep-sleeps. Optional: shake the magnet for an extra photo change (max 8 a day).

## Read in this order
1. `docs/design.md`: the approved design and bill of materials.
2. `docs/plan.md`: the 8-task build and test plan, with exact interfaces and test cases. Task 2 and Task 3 are done.
3. `docs/ledger.md`: what has been built, and every decision made along the way (lines with `Ruling:`).
4. `docs/datasheets/`: Good Display GDEH037E01 panel and DESPI-E01 adapter datasheets.
5. `firmware/reference/GDEH037E01_idf.c`: Good Display's ESP-IDF sample for the panel (reference only; to be ported to Arduino in Task 1).
6. `docs/phase2-custom-pcb.md`: a later, parked exploration. Do not build it now.

## Current state
- `server/` is built and tested (33 tests), with a Docker deploy behind the Cloudflare Tunnel Erik already runs on his server (`docker-compose.yml`, steps in `server/README.md`; not yet run on Erik's host). It keeps each original upload, re-renders all frames at start when the render settings change, shuffles the rotation, and serves the upload page (status, multi-upload, show next, magnet preview). Run them from `server/`: `pip install fastapi uvicorn pillow httpx python-multipart itsdangerous pytest` then `pytest`.
- Not done: Task 3 Step 5 (deploy behind HTTPS; needs Erik's host), and everything that needs hardware: Task 1 (bench bring-up) and Tasks 4 to 8 (firmware, setup mode, battery, case, shake). Erik has ordered the parts: XIAO ESP32-S3, GDEH037E01 panel with its DESPI-E01 adapter, a 303450 battery and an MPU6050.
- Firmware is an Arduino IDE sketch in `firmware/magnet/` (Erik's choice; Arduino-ESP32 core, board XIAO_ESP32S3). The PC-testable logic (`logic.c`/`logic.h`) for Tasks 4, 5, 6 and 8 is done; run from the repo root: `gcc -Wall -Wextra -Werror firmware/test/test_logic.c firmware/magnet/logic.c -o /tmp/t && /tmp/t`. Tunables are in `settings.h`; secrets go in git-ignored `secrets.h` (template `secrets.example.h`). `magnet.ino`, `firmware/bench` and all hardware code do not exist yet.

## Rules
- Follow the plan's interfaces and names exactly. Where the plan is wrong or silent, decide, and record a `Ruling:` line in `docs/ledger.md` with what it costs if wrong.
- Use TDD where the plan gives tests: write the test, watch it fail, then implement.
- Do not assume what the hardware will do. Two things are assumptions until Task 1 measures them: the nibble order and orientation of a frame (`HIGH_NIBBLE_IS_LEFT` in `server/imaging.py`) and the pin map in the plan (check it against Seeed's XIAO ESP32-S3 pinout). Panel power, refresh time and the 32-pin versus 24-pin FPC fit are also unconfirmed.
- Erik prefers to be asked before assumptions are made. If a choice changes what gets built, ask him.
- Never commit secrets. The server takes `DEVICE_TOKEN`, `UPLOAD_PASSWORD_HASH`, `SESSION_SECRET`, `DATA_DIR` and `LOW_BATTERY_WEBHOOK_URL` from the environment; see `server/README.md`.
- Known deferred item: `/login` has no attempt throttling (behind Cloudflare, the client IP is in `CF-Connecting-IP`).
