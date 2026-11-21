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
