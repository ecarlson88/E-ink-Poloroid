/* Tunable, non-secret settings for the magnet firmware. Committed to git.
 * Secrets (Wi-Fi password, device token, server URL) go in secrets.h, which
 * is git-ignored; copy secrets.example.h to start.
 *
 * Every value is wrapped in #ifndef so the PC tests can override it with -D. */
#pragma once

/* Seconds to sleep after a failed wake (Task 4). Set to 30 for bench tests. */
#ifndef FAIL_RETRY_SECONDS
#define FAIL_RETRY_SECONDS 3600u
#endif

/* Which pixel of a byte is the left one. Must match HIGH_NIBBLE_IS_LEFT in
 * server/imaging.py. An assumption until Task 1 Step 4 checks it. */
#ifndef HIGH_NIBBLE_IS_LEFT
#define HIGH_NIBBLE_IS_LEFT 1
#endif

/* Battery below this is low (Task 6). Matches LOW_BATTERY_MV in server/app.py. */
#ifndef LOW_BATTERY_MV
#define LOW_BATTERY_MV 3500
#endif

/* Consecutive failed wakes before setup mode (Task 5). */
#ifndef SETUP_AFTER_FAILURES
#define SETUP_AFTER_FAILURES 3
#endif

/* Task 5 (Erik): a second press of the reset button within this time opens setup mode. */
#ifndef DOUBLE_PRESS_WINDOW_MS
#define DOUBLE_PRESS_WINDOW_MS 5000u
#endif
