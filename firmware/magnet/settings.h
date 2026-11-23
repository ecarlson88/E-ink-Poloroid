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

/* Task 5 (Erik): hold the edge button (D5, acrylic case) this long for setup mode;
 * a shorter press shows the next photo. */
#ifndef SETUP_HOLD_MS
#define SETUP_HOLD_MS 5000u
#endif

/* Task 5: the edge button still down after this long is stuck (jammed against the door
 * seal): no setup, no photo, and D5 is left out of the wake pins until it lets go. */
#ifndef BUTTON_STUCK_MS
#define BUTTON_STUCK_MS 15000u
#endif

/* Which wake pins are wired on this build. Unwired pins would float in deep sleep and
 * wake the magnet, so they are never armed. 1 only for the acrylic case (edge button on
 * D5) and for builds with the MPU6050 fitted (Task 8, interrupt on D9). */
#ifndef HAS_EDGE_BUTTON
#define HAS_EDGE_BUTTON 0
#endif
#ifndef HAS_MPU
#define HAS_MPU 0
#endif
