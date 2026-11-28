/* Setup mode (Task 5): the open hotspot FridgeMagnet-Setup with a page to choose Wi-Fi. */
#pragma once

#include <stdint.h>

/* Starts the hotspot, a catch-all DNS (so phones open the page by themselves) and a page that
 * lists nearby networks and takes a network, its password and an optional pairing code.
 * Saves the Wi-Fi to NVS once the magnet has joined it; with a code, pairs (net_pair) and
 * shows the magnet's name or what went wrong. Returns true once joined and, if a code was
 * given or the magnet has no key yet, paired; false after timeout_s. */
bool setup_portal_run(uint32_t timeout_s);
