/* Wi-Fi and the server (Task 4; pairing for Task 5). */
#pragma once

#include <Arduino.h>
#include <stddef.h>
#include <stdint.h>

/* Join a network as a station. True once connected, false after timeout_ms. */
bool wifi_join(const char *ssid, const char *pass, uint32_t timeout_ms);

/* GET /api/device/next?bat_mv=... over HTTPS with this magnet's key. Fills buf (cap bytes)
 * and sets *out_len and *http_status (negative: no HTTP answer). True only for a full frame
 * (frame_ok). A reply longer than cap reports cap + 1 bytes. */
bool net_fetch_frame(uint8_t *buf, size_t cap, size_t *out_len, int bat_mv, int *http_status);

/* The magnet's key: NVS namespace "server", key "token", else secrets.h's DEVICE_TOKEN.
 * Empty when the magnet was never paired. */
String net_token(void);

/* Task 5: trade a pairing code for this magnet's key (POST /api/device/pair) and save the
 * key to NVS. On success name is the magnet's name on the page; on failure err says why, in
 * words for the setup page. Needs Wi-Fi. */
bool net_pair(const char *code, String &name, String &err);

/* Saved Wi-Fi (NVS namespace "wifi"), else secrets.h's development network. */
void net_wifi_creds(String &ssid, String &pass);
void net_save_wifi(const String &ssid, const String &pass);
