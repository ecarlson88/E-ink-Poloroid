/* Copy to secrets.h (git-ignored) and fill in. Never commit secrets.h. */
#pragma once

/* The server's base address; the firmware adds /api/device/next and /api/device/pair. */
#define SERVER_URL "https://magnet.example.com"
/* Bench only: a key to use before the magnet is paired. A real magnet gets its key by
   pairing (a code typed on its setup page) and keeps it in NVS. Leave "" to rely on pairing. */
#define DEVICE_TOKEN ""

/* Development Wi-Fi, used until setup mode (Task 5) saves the parents' network. */
#define WIFI_SSID "your-ssid"
#define WIFI_PASS "your-password"
