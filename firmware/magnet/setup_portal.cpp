/* Setup mode: see setup_portal.h.
 *
 * The ESP32 has one radio, so its hotspot must move to the home network's channel when it
 * joins it, which can drop the phone for a moment. To make that less likely the hotspot
 * starts on the channel of the strongest network nearby (most often the home one). Checked
 * on the bench in Task 5 Step 5. */
#include <Arduino.h>
#include <DNSServer.h>
#include <Preferences.h>
#include <WebServer.h>
#include <WiFi.h>

#include "net.h"
#include "settings.h"
#include "setup_portal.h"

static const char *AP_NAME = "FridgeMagnet-Setup";
static const int MAX_NETWORKS = 20;

static WebServer *s_server;
static String s_networks[MAX_NETWORKS];
static int s_network_count = 0;
static bool s_done = false;

static String html_escape(const String &s)
{
    String out;
    for (size_t i = 0; i < s.length(); i++) {
        char c = s[i];
        if (c == '&') out += "&amp;";
        else if (c == '<') out += "&lt;";
        else if (c == '>') out += "&gt;";
        else if (c == '"') out += "&quot;";
        else if (c == '\'') out += "&#39;";
        else out += c;
    }
    return out;
}

/* Scan before the hotspot starts. Returns the channel of the strongest network (1 if none). */
static int scan_networks(void)
{
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    int n = WiFi.scanNetworks();
    int best_channel = 1, best_rssi = -1000;
    s_network_count = 0;
    /* Strongest first; skip hidden and repeated names (one name, several access points). */
    for (int pass = 0; pass < n && s_network_count < MAX_NETWORKS; pass++) {
        int pick = -1;
        for (int i = 0; i < n; i++) {
            String name = WiFi.SSID(i);
            if (name.length() == 0) continue;
            bool seen = false;
            for (int k = 0; k < s_network_count; k++) seen |= (s_networks[k] == name);
            if (seen) continue;
            if (pick < 0 || WiFi.RSSI(i) > WiFi.RSSI(pick)) pick = i;
        }
        if (pick < 0) break;
        s_networks[s_network_count++] = WiFi.SSID(pick);
        if (WiFi.RSSI(pick) > best_rssi) {
            best_rssi = WiFi.RSSI(pick);
            best_channel = WiFi.channel(pick);
        }
    }
    WiFi.scanDelete();
    return best_channel;
}

static const char PAGE_HEAD[] =
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Photo magnet setup</title><style>"
    "body{font:18px/1.4 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:20px 16px;"
    "background:#fff;color:#1d1d1f}main{max-width:420px;margin:0 auto}"
    "h1{font-size:26px;margin:0 0 12px}label{display:block;margin:16px 0 6px;font-weight:600}"
    "select,input{box-sizing:border-box;width:100%;font:inherit;padding:12px;border:1px solid #bbb;"
    "border-radius:10px;min-height:48px;background:#fff;color:inherit}"
    "button{width:100%;margin-top:22px;font:inherit;font-weight:600;padding:14px;border:0;"
    "border-radius:10px;background:#1d6fd6;color:#fff;min-height:52px}"
    ".hint{color:#555;font-size:15px;margin:4px 0 0}.err{background:#fde8e8;color:#8a1c1c;"
    "padding:12px;border-radius:10px}.ok{background:#e6f4ea;color:#1e5b2f;padding:12px;border-radius:10px}"
    "</style></head><body><main>";
static const char PAGE_TAIL[] = "</main></body></html>";

static void send_form(const String &message, bool is_error)
{
    String page = PAGE_HEAD;
    page += "<h1>Photo magnet Wi-Fi</h1>";
    if (message.length())
        page += String("<p class='") + (is_error ? "err" : "ok") + "'>" + html_escape(message) + "</p>";
    page += "<form method='post' action='/save'><label for='ssid'>Your home Wi-Fi</label>"
            "<select id='ssid' name='ssid'>";
    for (int i = 0; i < s_network_count; i++)
        page += "<option>" + html_escape(s_networks[i]) + "</option>";
    page += "<option value=''>Other (type it below)</option></select>"
            "<input name='ssid_other' placeholder='Network name, if not in the list' autocapitalize='none'>"
            "<label for='pass'>Wi-Fi password</label>"
            "<input id='pass' name='pass' type='password' autocapitalize='none' autocomplete='off'>"
            "<label for='code'>Pairing code</label>"
            "<input id='code' name='code' autocapitalize='characters' autocomplete='off' placeholder='Only if you were given one'>"
            "<p class='hint'>Leave it empty if the magnet already showed photos before.</p>"
            "<button type='submit'>Save</button></form>";
    page += PAGE_TAIL;
    s_server->send(200, "text/html", page);
}

static void handle_save(void)
{
    String ssid = s_server->arg("ssid_other");
    ssid.trim();
    if (ssid.length() == 0) ssid = s_server->arg("ssid");
    String pass = s_server->arg("pass");
    String code = s_server->arg("code");
    code.trim();
    if (ssid.length() == 0) {
        send_form("Choose your Wi-Fi network first.", true);
        return;
    }

    Serial.printf("[setup] joining %s\n", ssid.c_str());
    WiFi.begin(ssid.c_str(), pass.c_str());
    uint32_t start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < WIFI_TIMEOUT_MS) delay(100);
    if (WiFi.status() != WL_CONNECTED) {
        WiFi.disconnect(false);
        send_form("Could not join \"" + ssid + "\". Check the password and try again.", true);
        return;
    }
    net_save_wifi(ssid, pass);

    String name, err;
    if (code.length() > 0) {
        if (!net_pair(code.c_str(), name, err)) {
            send_form("Wi-Fi saved. " + err, true);
            return;
        }
    } else if (net_token().length() == 0) {
        send_form("Wi-Fi saved. This magnet is not paired yet: type the pairing code from the photo page.", true);
        return;
    }

    String page = PAGE_HEAD;
    page += "<h1>All set</h1><p class='ok'>Connected to " + html_escape(ssid) + ".";
    if (name.length()) page += " This is <b>" + html_escape(name) + "</b>.";
    page += "</p><p>The magnet will show a new photo in about a minute. You can close this page.</p>";
    page += PAGE_TAIL;
    s_server->send(200, "text/html", page);
    s_done = true;
}

static void handle_other(void)
{
    /* Phones probe a known address to find a sign-in page; send every unknown address to ours. */
    s_server->sendHeader("Location", "http://" + WiFi.softAPIP().toString() + "/", true);
    s_server->send(302, "text/plain", "");
}

bool setup_portal_run(uint32_t timeout_s)
{
    int channel = scan_networks();
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP(AP_NAME, NULL, channel);
    delay(200);
    DNSServer dns;
    dns.start(53, "*", WiFi.softAPIP());
    WebServer server(80);
    s_server = &server;
    s_done = false;
    server.on("/", HTTP_GET, []() { send_form("", false); });
    server.on("/save", HTTP_POST, handle_save);
    server.onNotFound(handle_other);
    server.begin();
    Serial.printf("[setup] hotspot %s on channel %d, %d networks listed\n", AP_NAME, channel, s_network_count);

    uint32_t start = millis();
    uint32_t done_at = 0;
    while (millis() - start < timeout_s * 1000UL) {
        dns.processNextRequest();
        server.handleClient();
        if (s_done && done_at == 0) done_at = millis();
        if (done_at && millis() - done_at > 3000) break;   /* let the phone load the result page */
        delay(2);
    }
    server.stop();
    dns.stop();
    s_server = NULL;
    WiFi.softAPdisconnect(true);
    WiFi.mode(WIFI_STA);
    Serial.printf("[setup] %s\n", s_done ? "done" : "timed out");
    return s_done;
}
