/* Host tests for firmware/magnet/logic.c. Plain C, no ESP-IDF.
 * Build and run from the repo root:
 *   gcc -Wall -Wextra -Werror firmware/test/test_logic.c firmware/magnet/logic.c -o /tmp/t && /tmp/t
 */
#include <stdio.h>
#include <string.h>

#include "../magnet/logic.h"

static int failures = 0;

#define CHECK(expr)                                                     \
    do {                                                                \
        if (!(expr)) {                                                  \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr);      \
            failures++;                                                 \
        }                                                               \
    } while (0)

/* Task 4: only a full 200 response may reach the panel. */
static void test_frame_ok(void)
{
    CHECK(frame_ok(200, 172800) == true);
    CHECK(frame_ok(200, 172799) == false);
    CHECK(frame_ok(200, 0) == false);
    CHECK(frame_ok(204, 0) == false);
    CHECK(frame_ok(401, 172800) == false);
    CHECK(frame_ok(500, 172800) == false);
}

/* Task 4: a day on success, FAIL_RETRY_SECONDS after a failure. */
static void test_next_sleep_seconds(void)
{
    CHECK(next_sleep_seconds(true, 0) == 86400);
    CHECK(next_sleep_seconds(false, 1) == FAIL_RETRY_SECONDS);
}

/* Task 5: setup mode from the third consecutive failure. */
static void test_should_enter_setup(void)
{
    CHECK(should_enter_setup(2) == false);
    CHECK(should_enter_setup(3) == true);
    CHECK(should_enter_setup(10) == true);
}

/* Task 6: low below 3500 mV. */
static void test_battery_low(void)
{
    CHECK(battery_low(3499) == true);
    CHECK(battery_low(3500) == false);
}

/* Task 6: the icon is 48x24 px, 16 px from the top and right edges. In the
 * packed frame (2 px per byte, 240 bytes per row) that is rows 16..39 and
 * bytes 208..231 of each row. */
#define ROW_BYTES (480 / 2)
#define ICON_ROW0 16
#define ICON_ROWS 24
#define ICON_BYTE0 ((480 - 16 - 48) / 2)
#define ICON_BYTES (48 / 2)

static bool in_icon(size_t i)
{
    size_t row = i / ROW_BYTES, col = i % ROW_BYTES;
    return row >= ICON_ROW0 && row < ICON_ROW0 + ICON_ROWS &&
           col >= ICON_BYTE0 && col < ICON_BYTE0 + ICON_BYTES;
}

static uint8_t frame_a[FRAME_BYTES], frame_b[FRAME_BYTES];

static void test_overlay_low_battery(void)
{
    memset(frame_a, 0x11, sizeof frame_a);
    overlay_low_battery(frame_a);

    int outside_changed = 0, inside_changed = 0;
    for (size_t i = 0; i < FRAME_BYTES; i++) {
        if (frame_a[i] == 0x11) continue;
        if (in_icon(i)) inside_changed++; else outside_changed++;
    }
    CHECK(outside_changed == 0);
    CHECK(inside_changed > 0); /* the icon actually draws something */

    memcpy(frame_b, frame_a, sizeof frame_b);
    overlay_low_battery(frame_b);
    CHECK(memcmp(frame_a, frame_b, FRAME_BYTES) == 0); /* idempotent */
}

/* Task 8: fill n samples with 50 mg noise, then place peaks. */
#define SHAKE_N 150
static int16_t samples[SHAKE_N];

static void noise(void)
{
    for (size_t i = 0; i < SHAKE_N; i++) samples[i] = (int16_t)(i % 2 ? 50 : 10);
}

static void test_shake_is_deliberate(void)
{
    noise();
    CHECK(shake_is_deliberate(samples, SHAKE_N, 1500, 4) == false);

    noise();
    samples[70] = 4000; /* a door slam: one big spike */
    CHECK(shake_is_deliberate(samples, SHAKE_N, 1500, 4) == false);

    noise();
    for (int k = 0; k < 4; k++) samples[20 + 20 * k] = 2000;
    CHECK(shake_is_deliberate(samples, SHAKE_N, 1500, 4) == true);

    noise();
    for (int k = 0; k < 4; k++) samples[20 + 3 * k] = 2000; /* too close: one peak */
    CHECK(shake_is_deliberate(samples, SHAKE_N, 1500, 4) == false);
}

static void test_shake_allowed(void)
{
    CHECK(shake_allowed(7, 600, 8, 300) == true);
    CHECK(shake_allowed(8, 600, 8, 300) == false);
    CHECK(shake_allowed(2, 100, 8, 300) == false);
}

/* Task 8: a shake must not move the daily wake. */
static void test_remaining_sleep_seconds(void)
{
    CHECK(remaining_sleep_seconds(100000000, 40000000) == 60);
    CHECK(remaining_sleep_seconds(100000000, 100000001) == 0);
    CHECK(remaining_sleep_seconds(100000000, 100000000) == 0);
}

/* Task 5 (Erik): setup mode is a double press of the XIAO reset button through the rear
 * pinhole. A reset press starts the chip like power-on; deep-sleep wakes never check. */
static void test_boot_action(void)
{
    /* First power-on (or first press): arm the double-press window, then run normally. */
    CHECK(boot_action(WAKE_POWER_ON, false) == BOOT_ARM_DOUBLE_PRESS);
    /* A second press while the window's flag is still set: setup mode. */
    CHECK(boot_action(WAKE_POWER_ON, true) == BOOT_SETUP);
    /* The daily timer (and a shake) never look at the flag. */
    CHECK(boot_action(WAKE_DEEP_SLEEP, false) == BOOT_NORMAL);
    CHECK(boot_action(WAKE_DEEP_SLEEP, true) == BOOT_NORMAL);
    /* Brownout, watchdog, panic: run normally, no setup. */
    CHECK(boot_action(WAKE_OTHER, true) == BOOT_NORMAL);
    CHECK(boot_action(WAKE_OTHER, false) == BOOT_NORMAL);
}

/* Task 5 (Erik): the edge button on D5. A short press shows the next photo; holding it
 * SETUP_HOLD_MS (5 s) and letting go opens setup mode. A bump from a door slam reads as a
 * short press. A button still down after BUTTON_STUCK_MS is stuck: no setup, no photo. */
static void test_button_action(void)
{
    CHECK(button_action(0, true) == BUTTON_NEXT_PHOTO);               /* bump or tap */
    CHECK(button_action(4999, true) == BUTTON_NEXT_PHOTO);
    CHECK(button_action(SETUP_HOLD_MS, true) == BUTTON_SETUP);        /* 5000 */
    CHECK(button_action(BUTTON_STUCK_MS - 1, true) == BUTTON_SETUP);
    CHECK(button_action(BUTTON_STUCK_MS, false) == BUTTON_STUCK);     /* never let go */
}

/* Which pins may wake the magnet. Unwired pins never (they would float); a button that
 * is down now is left out, so a stuck button cannot wake it in a loop. */
static void test_wake_pins(void)
{
    CHECK(wake_pins(false, false, false) == 0);                       /* compact or v1, no MPU */
    CHECK(wake_pins(false, true, false) == 0);                        /* unwired D5 reads low: ignore */
    CHECK(wake_pins(true, false, false) == WAKE_PIN_D5);
    CHECK(wake_pins(true, true, false) == 0);                         /* stuck button */
    CHECK(wake_pins(false, false, true) == WAKE_PIN_D9);
    CHECK(wake_pins(true, false, true) == (WAKE_PIN_D5 | WAKE_PIN_D9));
    CHECK(wake_pins(true, true, true) == WAKE_PIN_D9);
}

int main(void)
{
    test_frame_ok();
    test_next_sleep_seconds();
    test_should_enter_setup();
    test_battery_low();
    test_overlay_low_battery();
    test_shake_is_deliberate();
    test_shake_allowed();
    test_remaining_sleep_seconds();
    test_boot_action();
    test_button_action();
    test_wake_pins();
    if (failures) {
        printf("%d check(s) failed\n", failures);
        return 1;
    }
    printf("all logic tests passed\n");
    return 0;
}
