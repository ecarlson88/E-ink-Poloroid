/* Panel driver for the GDEH037E01 through the DESPI-E01 adapter (Task 4), ported from
 * Good Display's ESP-IDF sample (firmware/reference/GDEH037E01_idf.c). */
#pragma once

#include <stddef.h>
#include <stdint.h>

/* Draw one packed frame. Returns false and leaves the panel untouched unless
 * len == 172800; otherwise runs reset, init, write, power on, refresh, power off and
 * panel deep sleep, and returns false if any BUSY wait timed out. */
bool epd_show_frame(const uint8_t *frame, size_t len);

/* Before the ESP32 deep-sleeps: hold the panel's RST and CS lines high, so a floating
 * line cannot wake the panel out of its own deep sleep. */
void epd_prepare_sleep(void);

/* Bench logging (RESULTS.md): the last refresh (command 0x12 to BUSY release) and the
 * last frame data transfer, in milliseconds. */
uint32_t epd_last_refresh_ms(void);
uint32_t epd_last_transfer_ms(void);
