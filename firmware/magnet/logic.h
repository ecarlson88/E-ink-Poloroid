/* Pure decisions for the magnet firmware. No Arduino or ESP-IDF calls here,
 * so this file builds on the PC with plain gcc (see firmware/test/test_logic.c). */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "settings.h"

#ifdef __cplusplus
extern "C" {  /* magnet.ino is C++; logic.c is C */
#endif

#define FRAME_BYTES 172800u
#define DAILY_SLEEP_SECONDS 86400u

/* True only for an HTTP 200 carrying exactly one full frame. */
bool frame_ok(int http_status, size_t len);

/* Seconds to deep-sleep after a wake. */
uint32_t next_sleep_seconds(bool success, int consecutive_failures);

/* Task 5: true once consecutive failed wakes reach SETUP_AFTER_FAILURES (3). */
bool should_enter_setup(int consecutive_failures);

/* Task 6: true below LOW_BATTERY_MV (3500). */
bool battery_low(int mv);

/* Task 6: stamp a 48x24 low-battery icon into a packed frame, 16 px from the
 * top and right edges. Touches only bytes inside the icon; idempotent. */
void overlay_low_battery(uint8_t *frame);

/* Task 8: dev_mg[i] = |acceleration magnitude - 1000 mg| sampled at 100 Hz.
 * A peak is a rising crossing of threshold_mg at least 8 samples after the
 * previous peak. True when peaks >= min_peaks. */
bool shake_is_deliberate(const int16_t *dev_mg, size_t n, int16_t threshold_mg, int min_peaks);

/* Task 8: true when shakes_today < cap and seconds_since_last >= min_gap_s. */
bool shake_allowed(int shakes_today, uint32_t seconds_since_last, int cap, uint32_t min_gap_s);

/* Task 8: seconds until deadline_us, 0 if it has passed. */
uint32_t remaining_sleep_seconds(uint64_t deadline_us, uint64_t now_us);

/* Task 5 (Erik): a double press of the reset button (rear pinhole) opens setup mode.
 * main reads the reset reason and an NVS flag, and acts on the result:
 *   BOOT_ARM_DOUBLE_PRESS: set the flag, wait DOUBLE_PRESS_WINDOW_MS, clear it, run normally
 *   BOOT_SETUP: clear the flag, run setup mode
 *   BOOT_NORMAL: run normally (fetch, draw, sleep) */
typedef enum { WAKE_POWER_ON, WAKE_DEEP_SLEEP, WAKE_OTHER } wake_kind_t;
typedef enum { BOOT_NORMAL, BOOT_ARM_DOUBLE_PRESS, BOOT_SETUP } boot_action_t;
boot_action_t boot_action(wake_kind_t wake, bool double_press_flag);

#ifdef __cplusplus
}
#endif
