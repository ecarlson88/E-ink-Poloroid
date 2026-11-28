/* Wi-Fi and the server: see net.h. HTTPS uses the core's built-in Mozilla root bundle
 * (useBuiltinCACertBundle, Arduino-ESP32 4.0.0 or later), which covers the certificates
 * Cloudflare serves. */
#include <Arduino.h>
#include <HTTPClient.h>
#include <NetworkClientSecure.h>
#include <Preferences.h>
#include <WiFi.h>

#include "logic.h"
#include "net.h"
#include "secrets.h"

static const uint32_t HTTP_TIMEOUT_MS = 15000;
static const uint32_t STALL_TIMEOUT_MS = 10000;   /* no bytes for this long: give up */

bool wifi_join(const char *ssid, const char *pass, uint32_t timeout_ms)
{
    if (ssid == NULL || ssid[0] == '\0') return false;
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, pass);
    uint32_t start = millis();
    while (WiFi.status() != WL_CONNECTED) {
        if (millis() - start > timeout_ms) {
            WiFi.disconnect(true);
            return false;
        }
        delay(50);
    }
    return true;
}

String net_token(void)
{
    Preferences p;
    String token;
    if (p.begin("server", true)) {
        token = p.getString("token", "");
        p.end();
    }
    if (token.length() == 0) token = DEVICE_TOKEN;
    return token;
}

void net_wifi_creds(String &ssid, String &pass)
{
    Preferences p;
    ssid = "";
    pass = "";
    if (p.begin("wifi", true)) {
        ssid = p.getString("ssid", "");
        pass = p.getString("pass", "");
        p.end();
    }
    if (ssid.length() == 0) {
        ssid = WIFI_SSID;
        pass = WIFI_PASS;
    }
}

void net_save_wifi(const String &ssid, const String &pass)
{
    Preferences p;
    p.begin("wifi", false);
    p.putString("ssid", ssid);
    p.putString("pass", pass);
    p.end();
}

bool net_fetch_frame(uint8_t *buf, size_t cap, size_t *out_len, int bat_mv, int *http_status)
{
    *out_len = 0;
    *http_status = -1;
    String token = net_token();
    if (token.length() == 0) return false;

    NetworkClientSecure client;
    client.useBuiltinCACertBundle();
    HTTPClient http;
    http.setTimeout(HTTP_TIMEOUT_MS);
    http.setConnectTimeout(HTTP_TIMEOUT_MS);
    String url = String(SERVER_URL) + "/api/device/next?bat_mv=" + String(bat_mv);
    if (!http.begin(client, url)) return false;
    http.addHeader("Authorization", "Bearer " + token);

    int code = http.GET();
    *http_status = code;
    if (code != 200) {
        http.end();
        return false;
    }
    int size = http.getSize();              /* the server sends Content-Length */
    if (size > (int)cap) {
        *out_len = cap + 1;
        http.end();
        return false;
    }
    NetworkClient *stream = http.getStreamPtr();
    size_t got = 0;
    uint32_t last = millis();
    while (got < cap) {
        if (size >= 0 && got >= (size_t)size) break;
        size_t avail = stream->available();
        if (avail) {
            size_t want = avail < cap - got ? avail : cap - got;
            int n = stream->read(buf + got, want);
            if (n > 0) {
                got += (size_t)n;
                last = millis();
            }
        } else if (!http.connected() || millis() - last > STALL_TIMEOUT_MS) {
            break;
        } else {
            delay(1);
        }
    }
    if (got == cap && stream->available()) got = cap + 1;   /* longer than a frame */
    *out_len = got;
    http.end();
    return frame_ok(code, got);
}

/* The string value of "key" in a flat JSON object, with the common escapes undone. */
static bool json_string(const String &body, const char *key, String &out)
{
    String pattern = String("\"") + key + "\"";
    int i = body.indexOf(pattern);
    if (i < 0) return false;
    i = body.indexOf(':', i + pattern.length());
    if (i < 0) return false;
    i = body.indexOf('"', i + 1);
    if (i < 0) return false;
    out = "";
    for (int j = i + 1; j < (int)body.length(); j++) {
        char c = body[j];
        if (c == '"') return true;
        if (c != '\\' || j + 1 >= (int)body.length()) {
            out += c;
            continue;
        }
        char e = body[++j];
        if (e == 'n') out += '\n';
        else if (e == 't') out += '\t';
        else if (e == 'u' && j + 4 < (int)body.length()) {
            unsigned cp = (unsigned)strtoul(body.substring(j + 1, j + 5).c_str(), NULL, 16);
            j += 4;
            if (cp < 0x80) out += (char)cp;                      /* UTF-8, basic plane only */
            else if (cp < 0x800) { out += (char)(0xC0 | (cp >> 6)); out += (char)(0x80 | (cp & 0x3F)); }
            else { out += (char)(0xE0 | (cp >> 12)); out += (char)(0x80 | ((cp >> 6) & 0x3F));
                   out += (char)(0x80 | (cp & 0x3F)); }
        } else out += e;                                          /* \" \\ \/ */
    }
    return false;
}

bool net_pair(const char *code, String &name, String &err)
{
    String clean;                           /* codes are letters, digits and a dash */
    for (const char *p = code; *p; p++)
        if (isalnum((unsigned char)*p) || *p == '-') clean += *p;
    if (clean.length() == 0) {
        err = "Type the pairing code from the photo page.";
        return false;
    }

    NetworkClientSecure client;
    client.useBuiltinCACertBundle();
    HTTPClient http;
    http.setTimeout(HTTP_TIMEOUT_MS);
    if (!http.begin(client, String(SERVER_URL) + "/api/device/pair")) {
        err = "Could not reach the photo server.";
        return false;
    }
    http.addHeader("Content-Type", "application/json");
    int status = http.POST("{\"code\":\"" + clean + "\"}");
    String body = status > 0 ? http.getString() : String();
    http.end();

    String token;
    if (status == 200 && json_string(body, "token", token) && token.length() > 0) {
        json_string(body, "name", name);
        Preferences p;
        p.begin("server", false);
        p.putString("token", token);
        p.end();
        return true;
    }
    if (status == 401) err = "That pairing code is wrong or has expired. Make a new one on the photo page.";
    else if (status < 0) err = "Joined Wi-Fi, but could not reach the photo server.";
    else err = "The photo server answered " + String(status) + ". Try again later.";
    return false;
}
