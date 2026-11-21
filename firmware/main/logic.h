/* Pure decisions for the magnet firmware. No ESP-IDF calls here, so this
 * file builds on the PC with plain gcc (see firmware/test/test_logic.c). */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Under ESP-IDF the value comes from Kconfig (menuconfig); on the PC the
 * Kconfig default is used. */
#if __has_include("sdkconfig.h")
#include "sdkconfig.h"
#endif
#ifndef CONFIG_FAIL_RETRY_SECONDS
#define CONFIG_FAIL_RETRY_SECONDS 3600
#endif
#define FAIL_RETRY_SECONDS ((uint32_t)CONFIG_FAIL_RETRY_SECONDS)

#define FRAME_BYTES 172800u
#define DAILY_SLEEP_SECONDS 86400u

/* True only for an HTTP 200 carrying exactly one full frame. */
bool frame_ok(int http_status, size_t len);

/* Seconds to deep-sleep after a wake. */
uint32_t next_sleep_seconds(bool success, int consecutive_failures);
