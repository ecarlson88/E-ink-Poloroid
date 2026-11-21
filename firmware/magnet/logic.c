#include "logic.h"

bool frame_ok(int http_status, size_t len)
{
    return http_status == 200 && len == FRAME_BYTES;
}

uint32_t next_sleep_seconds(bool success, int consecutive_failures)
{
    /* The failure count is not used yet: Task 5 sends the device to setup
     * mode on the third failure, before this is called. */
    (void)consecutive_failures;
    return success ? DAILY_SLEEP_SECONDS : FAIL_RETRY_SECONDS;
}

bool should_enter_setup(int consecutive_failures)
{
    return consecutive_failures >= SETUP_AFTER_FAILURES;
}

bool battery_low(int mv)
{
    return mv < LOW_BATTERY_MV;
}

/* Panel nibble values (from Good Display's sample). */
#define NIB_BLACK 0x0
#define NIB_WHITE 0x1
#define NIB_RED 0x3

#define FRAME_W 480
#define ICON_W 48
#define ICON_H 24
#define ICON_MARGIN 16

static void set_pixel(uint8_t *frame, int x, int y, uint8_t nibble)
{
    uint8_t *b = &frame[(size_t)y * (FRAME_W / 2) + (size_t)x / 2];
    bool high = (x % 2 == 0) == (HIGH_NIBBLE_IS_LEFT != 0);
    *b = high ? (uint8_t)((*b & 0x0F) | (nibble << 4)) : (uint8_t)((*b & 0xF0) | nibble);
}

/* Icon, in icon coordinates: white background, a battery body with a 2 px
 * black outline (x 2..41, y 3..20), a terminal nub on the right
 * (x 42..45, y 8..15) and a red sliver of charge (x 6..11, y 7..16). */
static uint8_t icon_pixel(int x, int y)
{
    bool in_body = x >= 2 && x <= 41 && y >= 3 && y <= 20;
    bool in_inside = x >= 4 && x <= 39 && y >= 5 && y <= 18;
    bool in_nub = x >= 42 && x <= 45 && y >= 8 && y <= 15;
    bool in_charge = x >= 6 && x <= 11 && y >= 7 && y <= 16;
    if (in_charge) return NIB_RED;
    if ((in_body && !in_inside) || in_nub) return NIB_BLACK;
    return NIB_WHITE;
}

void overlay_low_battery(uint8_t *frame)
{
    const int x0 = FRAME_W - ICON_MARGIN - ICON_W, y0 = ICON_MARGIN;
    for (int y = 0; y < ICON_H; y++)
        for (int x = 0; x < ICON_W; x++)
            set_pixel(frame, x0 + x, y0 + y, icon_pixel(x, y));
}

#define SHAKE_MIN_PEAK_GAP 8 /* samples (80 ms at 100 Hz) */

bool shake_is_deliberate(const int16_t *dev_mg, size_t n, int16_t threshold_mg, int min_peaks)
{
    int peaks = 0;
    bool have_last = false;
    size_t last_peak = 0;
    for (size_t i = 0; i < n; i++) {
        bool above = dev_mg[i] >= threshold_mg;
        bool was_above = i > 0 && dev_mg[i - 1] >= threshold_mg;
        if (!above || was_above) continue;  /* not a rising crossing */
        if (have_last && i - last_peak < SHAKE_MIN_PEAK_GAP) continue;
        peaks++;
        have_last = true;
        last_peak = i;
    }
    return peaks >= min_peaks;
}

bool shake_allowed(int shakes_today, uint32_t seconds_since_last, int cap, uint32_t min_gap_s)
{
    return shakes_today < cap && seconds_since_last >= min_gap_s;
}

uint32_t remaining_sleep_seconds(uint64_t deadline_us, uint64_t now_us)
{
    if (now_us >= deadline_us) return 0;
    /* Round up so the device never wakes before the daily deadline. */
    return (uint32_t)((deadline_us - now_us + 999999u) / 1000000u);
}

boot_action_t boot_action(wake_kind_t wake, bool double_press_flag)
{
    if (wake != WAKE_POWER_ON) return BOOT_NORMAL;
    return double_press_flag ? BOOT_SETUP : BOOT_ARM_DOUBLE_PRESS;
}
