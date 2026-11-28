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

/* ---- Hardware code (epd.cpp, net.cpp, battery.cpp, setup_portal.cpp, magnet.ino) ----
 * Unused by the PC tests. Values marked "unconfirmed" are checked in Task 1. */

/* Pin map from the plan, checked against the XIAO_ESP32S3 variant in Arduino-ESP32 4.0.0
 * (pins_arduino.h): D1=GPIO2, D2=GPIO3, D3=GPIO4, D4=GPIO5, D5=GPIO6, D8=GPIO7, D9=GPIO8,
 * D10=GPIO9, D0=GPIO1. D9 is also the board's default SPI MISO, so the panel's SPI bus is
 * started with no MISO pin. */
#define PIN_EPD_MOSI D10
#define PIN_EPD_SCK  D8
#define PIN_EPD_CS   D1
#define PIN_EPD_DC   D2
#define PIN_EPD_RST  D3
#define PIN_EPD_BUSY D4
#define PIN_BATTERY  D0
#define PIN_BUTTON   D5
#define PIN_MPU_INT  D9

/* Panel SPI clock. Good Display's sample uses 2 MHz; Task 1 Step 5 tries 10 MHz. */
#ifndef EPD_SPI_HZ
#define EPD_SPI_HZ 2000000
#endif

/* BUSY is low while the panel works (datasheet pin table, and the sample's default);
 * the datasheet's Note 6-4 says the opposite. Unconfirmed until Task 1. */
#ifndef EPD_BUSY_ACTIVE_LOW
#define EPD_BUSY_ACTIVE_LOW 1
#endif

/* Wi-Fi join (Task 4): timeout per try and number of tries. */
#ifndef WIFI_TIMEOUT_MS
#define WIFI_TIMEOUT_MS 20000u
#endif
#ifndef WIFI_TRIES
#define WIFI_TRIES 2
#endif

/* Setup mode (Task 5): how long the portal stays open, and the sleep after it gives up. */
#ifndef PORTAL_TIMEOUT_S
#define PORTAL_TIMEOUT_S 600u
#endif
#ifndef SETUP_SLEEP_SECONDS
#define SETUP_SLEEP_SECONDS 86400u
#endif

/* Extra photos (edge button now, shake in Task 8): at most this many a day, this far apart. */
#ifndef EXTRA_PHOTO_CAP
#define EXTRA_PHOTO_CAP 8
#endif
#ifndef EXTRA_PHOTO_GAP_S
#define EXTRA_PHOTO_GAP_S 300u
#endif

/* Battery sense (Task 6): 2 x 1 MOhm divider, so the pin sees half the battery. */
#ifndef BATTERY_DIVIDER
#define BATTERY_DIVIDER 2
#endif
