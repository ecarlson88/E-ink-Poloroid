/* The fridge magnet (Tasks 4 to 6, and the edge button of Task 5).
 *
 * Board: XIAO_ESP32S3 in Arduino-ESP32 4.0.0 or later, PSRAM "OPI PSRAM". Copy
 * secrets.example.h to secrets.h first. Every decision is made by logic.c (tested on the PC:
 * firmware/test/test_logic.c); this file only reads the hardware and acts on the answers.
 *
 * Each wake: find out why we woke, do one thing, deep-sleep until the next daily deadline.
 *   timer or first power-up  -> the daily photo (failures retry; the third opens setup)
 *   reset button, once       -> the daily photo now (after a 5 s window for a second press)
 *   reset button, twice      -> setup mode
 *   edge button (D5)         -> a tap: one extra photo (capped); held 5 s: setup mode
 * Not built yet: Task 8's shake wake (HAS_MPU must stay 0). */
#include <Arduino.h>
#include <Preferences.h>
#include <WiFi.h>
#include <driver/rtc_io.h>
#include <esp_heap_caps.h>
#include <esp_rtc_time.h>
#include <esp_sleep.h>

#include "battery.h"
#include "epd.h"
#include "logic.h"
#include "net.h"
#include "settings.h"
#include "setup_portal.h"
#include "setup_screen.h"

#if HAS_MPU
#error "Task 8 (shake wake) is not written yet: keep HAS_MPU 0 in settings.h"
#endif

/* RTC memory survives deep sleep (not a reset button press, which starts them at 0). */
RTC_DATA_ATTR static uint64_t next_daily_deadline_us = 0;
RTC_DATA_ATTR static int shakes_today = 0;          /* extra photos today (button, later shake) */
RTC_DATA_ATTR static uint64_t last_shake_us = 0;

static const uint64_t US = 1000000ULL;
static Preferences prefs;                            /* NVS namespace "magnet" */

enum fetch_result { FETCH_OK, FETCH_FAILED, FETCH_NO_KEY };

static uint64_t now_us(void) { return esp_rtc_get_time_us(); }

static uint8_t *frame_buffer(void)
{
    static uint8_t *buf = NULL;
    if (buf) return buf;
    buf = (uint8_t *)heap_caps_malloc(FRAME_BYTES, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (buf) {
        Serial.println("[magnet] frame buffer in PSRAM");
    } else {
        buf = (uint8_t *)heap_caps_malloc(FRAME_BYTES, MALLOC_CAP_8BIT);
        Serial.printf("[magnet] frame buffer in internal RAM: %s\n", buf ? "ok" : "FAILED");
    }
    return buf;
}

/* Join Wi-Fi, fetch the next frame, draw it. The panel is touched only for a full frame. */
static fetch_result fetch_and_draw(int bat_mv)
{
    if (net_token().length() == 0) {
        Serial.println("[magnet] not paired: no key in NVS or secrets.h");
        return FETCH_NO_KEY;
    }
    String ssid, pass;
    net_wifi_creds(ssid, pass);
    bool joined = false;
    for (int i = 0; i < WIFI_TRIES && !joined; i++) joined = wifi_join(ssid.c_str(), pass.c_str(), WIFI_TIMEOUT_MS);
    if (!joined) {
        Serial.printf("[magnet] could not join %s; keeping old image\n", ssid.c_str());
        return FETCH_FAILED;
    }
    uint8_t *buf = frame_buffer();
    if (!buf) return FETCH_FAILED;
    size_t len = 0;
    int status = 0;
    bool ok = net_fetch_frame(buf, FRAME_BYTES, &len, bat_mv, &status);
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    if (!ok || !frame_ok(status, len)) {
        Serial.printf("[magnet] fetch failed (HTTP %d, %u bytes); keeping old image\n", status, (unsigned)len);
        return FETCH_FAILED;
    }
    Serial.printf("[magnet] got frame, battery %d mV\n", bat_mv);
    if (battery_low(bat_mv)) overlay_low_battery(buf);
    return epd_show_frame(buf, len) ? FETCH_OK : FETCH_FAILED;
}

static void set_failures(int n)
{
    prefs.putInt("wake_fail", n);
}

/* Draw the setup screen and run the portal. True if the magnet then drew a photo. */
static bool run_setup(void)
{
    Serial.println("[magnet] setup mode");
    epd_show_frame(setup_screen_frame, sizeof(setup_screen_frame));
    if (!setup_portal_run(PORTAL_TIMEOUT_S)) return false;
    if (fetch_and_draw(battery_read_mv()) != FETCH_OK) return false;
    set_failures(0);
    return true;
}

/* The daily wake (timer, first power-up, or a single reset press). */
static void run_daily(void)
{
    shakes_today = 0;
    int bat = battery_read_mv();             /* before Wi-Fi: the radio makes it sag */
    fetch_result r = fetch_and_draw(bat);
    uint64_t now = now_us();
    if (r == FETCH_OK) {
        set_failures(0);
        next_daily_deadline_us = now + (uint64_t)next_sleep_seconds(true, 0) * US;
        return;
    }
    int fails = prefs.getInt("wake_fail", 0) + 1;
    set_failures(fails);
    Serial.printf("[magnet] failed wake %d in a row\n", fails);
    if (r == FETCH_NO_KEY || should_enter_setup(fails)) {
        bool ok = run_setup();
        next_daily_deadline_us = now_us() + (ok ? (uint64_t)DAILY_SLEEP_SECONDS : (uint64_t)SETUP_SLEEP_SECONDS) * US;
        return;
    }
    next_daily_deadline_us = now + (uint64_t)next_sleep_seconds(false, fails) * US;
}

/* Setup started by hand (reset double press or a 5 s hold). The daily wake stays where it
 * was; if setup gives up, try a normal wake again after FAIL_RETRY_SECONDS, so a magnet put
 * into setup by mistake goes back to photos by itself. */
static void run_manual_setup(void)
{
    bool ok = run_setup();
    uint64_t now = now_us();
    if (ok && next_daily_deadline_us <= now) next_daily_deadline_us = now + (uint64_t)DAILY_SLEEP_SECONDS * US;
    if (!ok) {
        uint64_t retry = now + (uint64_t)FAIL_RETRY_SECONDS * US;
        if (next_daily_deadline_us <= now || retry < next_daily_deadline_us) next_daily_deadline_us = retry;
    }
}

static void handle_button(void)
{
    rtc_gpio_deinit((gpio_num_t)PIN_BUTTON);
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    uint32_t start = millis();
    while (digitalRead(PIN_BUTTON) == LOW && millis() - start < BUTTON_STUCK_MS) delay(10);
    uint32_t held = millis() - start;
    bool released = digitalRead(PIN_BUTTON) == HIGH;
    button_action_t action = button_action(held, released);
    Serial.printf("[magnet] button held %lu ms, %s\n", (unsigned long)held, released ? "released" : "stuck");

    if (action == BUTTON_SETUP) {
        run_manual_setup();
    } else if (action == BUTTON_NEXT_PHOTO) {
        uint64_t now = now_us();
        uint64_t since = last_shake_us ? (now - last_shake_us) / US : UINT32_MAX;
        uint32_t since_s = since > UINT32_MAX ? UINT32_MAX : (uint32_t)since;
        if (shake_allowed(shakes_today, since_s, EXTRA_PHOTO_CAP, EXTRA_PHOTO_GAP_S)) {
            /* Ruling: an extra photo that fails is not a failed daily wake (wake_fail unchanged). */
            fetch_and_draw(battery_read_mv());
            shakes_today++;
            last_shake_us = now;
        } else {
            Serial.printf("[magnet] extra photo not allowed (%d today)\n", shakes_today);
        }
    }
    /* BUTTON_STUCK: nothing; go_to_sleep leaves D5 unarmed while it stays down. */
}

static void go_to_sleep(void)
{
    epd_prepare_sleep();
    uint64_t now = now_us();
    if (next_daily_deadline_us <= now) next_daily_deadline_us = now + (uint64_t)FAIL_RETRY_SECONDS * US;
    uint32_t secs = remaining_sleep_seconds(next_daily_deadline_us, now);
    if (secs == 0) secs = 1;
    esp_sleep_enable_timer_wakeup((uint64_t)secs * US);

    bool button_low = false;
#if HAS_EDGE_BUTTON
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    delay(2);
    button_low = digitalRead(PIN_BUTTON) == LOW;
#endif
    uint8_t pins = wake_pins(HAS_EDGE_BUTTON, button_low, HAS_MPU);
    uint64_t mask = 0;
    if (pins & WAKE_PIN_D5) {
        mask |= 1ULL << PIN_BUTTON;
        rtc_gpio_pullup_en((gpio_num_t)PIN_BUTTON);
        rtc_gpio_pulldown_dis((gpio_num_t)PIN_BUTTON);
        esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_PERIPH, ESP_PD_OPTION_ON);   /* keep the pull-up powered */
    } else if (HAS_EDGE_BUTTON) {
        pinMode(PIN_BUTTON, INPUT);          /* stuck button: no pull-up current through it */
        rtc_gpio_pullup_dis((gpio_num_t)PIN_BUTTON);
    }
    if (pins & WAKE_PIN_D9) mask |= 1ULL << PIN_MPU_INT;
    if (mask) esp_sleep_enable_ext1_wakeup_io(mask, ESP_EXT1_WAKEUP_ANY_LOW);

    Serial.printf("[magnet] sleeping %lu s, wake pins 0x%x\n", (unsigned long)secs, pins);
    Serial.flush();
    esp_deep_sleep_start();
}

void setup()
{
    Serial.begin(115200);
    delay(50);
    prefs.begin("magnet", false);

    esp_reset_reason_t reason = esp_reset_reason();
    uint32_t causes = esp_sleep_get_wakeup_causes();   /* bit per esp_sleep_wakeup_cause_t */
    Serial.printf("[magnet] reset reason %d, wake causes 0x%lx\n", (int)reason, (unsigned long)causes);

    if (reason == ESP_RST_BROWNOUT) {
        /* Ruling: a brownout means the battery cannot carry the Wi-Fi burst. Retrying at once
         * would loop and drain it; sleep a day instead (the panel keeps the last photo). */
        Serial.println("[magnet] brownout: sleeping a day");
        next_daily_deadline_us = now_us() + (uint64_t)DAILY_SLEEP_SECONDS * US;
        go_to_sleep();
    }

    if (causes & (1UL << ESP_SLEEP_WAKEUP_EXT1)) {
        uint64_t woke = esp_sleep_get_ext1_wakeup_status();
        if (HAS_EDGE_BUTTON && (woke & (1ULL << PIN_BUTTON))) handle_button();
        go_to_sleep();
    }

    wake_kind_t wake = reason == ESP_RST_POWERON ? WAKE_POWER_ON
                     : reason == ESP_RST_DEEPSLEEP ? WAKE_DEEP_SLEEP : WAKE_OTHER;
    switch (boot_action(wake, prefs.getBool("dbl_press", false))) {
    case BOOT_SETUP:
        prefs.putBool("dbl_press", false);
        run_manual_setup();
        break;
    case BOOT_ARM_DOUBLE_PRESS:
        prefs.putBool("dbl_press", true);    /* a second press now lands in BOOT_SETUP */
        delay(DOUBLE_PRESS_WINDOW_MS);
        prefs.putBool("dbl_press", false);
        run_daily();
        break;
    case BOOT_NORMAL:
        run_daily();
        break;
    }
    go_to_sleep();
}

void loop() {}
