# SDD ledger — plan: Docs artifact "E-ink Fridge Magnet: Build and Test Plan" (https://claude.ai/artifact/9r1csgsiLLFapZ8JG1wFHG)
Pre-flight: Task 3 consumes Task 2 render_frame(photo: bytes) -> bytes, ValueError on bad input; signatures match.
Ruling: plan is a Docs artifact, not a repo file, so the sdd scripts are skipped and this ledger is kept by hand — nothing in the plan depends on them — none if wrong
Ruling: executing only Tasks 2 and 3 now; Tasks 1, 4-8 need hardware (case Task 7 needs measurements) — user asked for web interface and case while hardware ships — none if wrong
Task 2: Ruling: nibble order assumes the left pixel is the high nibble and rows run top to bottom (HIGH_NIBBLE_IS_LEFT flag) — Task 1 Step 4 settles it on the bench — flip one constant if wrong
Task 2: Ruling: explicit 50 MP check before decode, because Pillow only warns until 2x its limit — plan says reject above 50 MP — none
Task 2: complete (commits f355468..a1db128, tests: pytest → 6 passed)
Task 3: Ruling: create_app() factory (run with uvicorn --factory) and https_only session cookie, tests use an https base URL — keeps the cookie Secure in production — none
Task 3: Ruling: stored frames are rendered at upload time (files under DATA_DIR/frames), rotation cursor and battery streak live in one SQLite state row — fits the plan contract — none
Task 3: Steps 1-4 and 6 complete (commits a1db128..63cd857, tests: pytest → 16 passed); Step 5 (deploy behind TLS and curl-verify) is pending because it needs Erik's host
Final: minor (deferred): no login attempt throttling on /login — scrypt slows guessing but an internet-exposed page should rate-limit
Task 4: Ruling: FAIL_RETRY_SECONDS is a macro in logic.h fed by CONFIG_FAIL_RETRY_SECONDS from sdkconfig.h when present (`__has_include`), else 3600, so logic.c builds unchanged on the PC and under ESP-IDF — if the IDF build does not see sdkconfig.h from logic.h, the retry falls back to 3600 s silently; check the logged sleep time in Step 5
Task 4: Ruling: next_sleep_seconds ignores consecutive_failures (every failure retries after FAIL_RETRY_SECONDS); the third failure is handled by Task 5's setup mode before this is called — if a backoff is wanted later, only this function changes
Task 4: Steps 1-3 complete (tests: gcc firmware/test/test_logic.c firmware/main/logic.c → all logic tests passed; also with -DCONFIG_FAIL_RETRY_SECONDS=30); Steps 4-8 need hardware
Ruling (Erik): firmware moves from ESP-IDF to the Arduino IDE (Arduino-ESP32 core). firmware/main became the sketch folder firmware/magnet (magnet.ino arrives in Task 4 Step 4); Kconfig values became settings.h (committed, each value #ifndef so PC tests can override with -D) and secrets.h (git-ignored, template secrets.example.h); net and mpu6050 functions return bool instead of esp_err_t; plan.md updated to match
Ruling: logic.h wraps its declarations in extern "C" because magnet.ino is C++ and logic.c is C — without it the Arduino link fails, caught at first compile
Task 5: Steps 1-2 complete (should_enter_setup, threshold SETUP_AFTER_FAILURES = 3 in settings.h)
Task 6: Ruling: icon design is a white 48x24 box, black battery outline with a nub on the right, red sliver of charge; drawn per pixel through HIGH_NIBBLE_IS_LEFT (settings.h, must match server/imaging.py) — if Task 1 flips the nibble order or orientation, flip that setting too or the icon lands mirrored or in the wrong corner. Checked visually by decoding through the server's PALETTE
Task 6: Steps 1-2 complete (battery_low, overlay_low_battery; plan tests plus "the icon draws something")
Task 8: Ruling: a sample above threshold at index 0 counts as a rising crossing (nothing before it) — at most one extra peak per window — none
Task 8: Ruling: remaining_sleep_seconds rounds up to whole seconds so the device never wakes before the daily deadline — wakes up to 1 s late — none
Task 8: Steps 1-2 complete (shake_is_deliberate, shake_allowed, remaining_sleep_seconds)
Firmware logic tests: gcc -Wall -Wextra -Werror firmware/test/test_logic.c firmware/magnet/logic.c → all logic tests passed (also with -DHIGH_NIBBLE_IS_LEFT=0 -DFAIL_RETRY_SECONDS=30)
Task 3 follow-up (Erik): keep originals. Uploads are stored as-is under DATA_DIR/originals/<id> next to the frame. Ruling: frames are re-rendered automatically at server start when imaging.render_key() (palette, nibble order, size, RENDER_VERSION) differs from the key stored in the state row — no manual step after palette tuning or a nibble flip; restart the container — costs a few seconds per photo at that one start
Ruling: the photo row is committed only after both files are written (atomic tmp+rename), fixing an orphan row on a failed write — none
Ruling: no SQLite migration for the new state.render_key column, because the server has never been deployed — a database from before this change would fail at start; delete it (it holds only test data)
Task 3 follow-up: tests: pytest → 20 passed
Task 3 Step 5 (Erik: deploy with Docker): server/Dockerfile (python:3.13-slim, non-root uid 10001, healthcheck on /) and root docker-compose.yml (env from git-ignored .env, template .env.example; port bound to 127.0.0.1:8000 for a proxy on the same host). Verified here with docker compose: 401 without/with wrong token, 204 empty, login with a $$-escaped hash in .env, upload, 200 with 172,800 bytes, data kept across restart, healthy. HTTPS proxy part waits on Erik's Cloudflare/Caddy answer
Ruling: data in a named Docker volume (magnet-data), not a ./data bind mount — the bind mount failed here (folder created root-owned, container runs non-root) — backups need `docker compose cp` instead of copying a folder
Ruling: Python dependencies are not version-pinned in the image (same as pyproject.toml) — a future breaking FastAPI/Pillow release could break a rebuild; pin with a lock file if that happens
