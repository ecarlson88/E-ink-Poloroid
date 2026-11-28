/* Bench bring-up for the panel (Task 1 Steps 3 to 7). Board: XIAO_ESP32S3, PSRAM "OPI PSRAM",
 * Arduino-ESP32 4.0.0 or later. Open the Serial Monitor at 115200 and send one letter:
 *
 *   c  corner test frame (Step 4: orientation and nibble order; see tools/make_test_frames.py)
 *   s  six-color swatch (Task 4 Step 6)
 *   w  all white          k  all black
 *   m  write mode: one byte per CS pulse as in Good Display's sample, or 4,092-byte batches (Step 5)
 *   f  SPI clock: 2 -> 4 -> 8 -> 10 MHz -> 2 (Step 5)
 *   p  detect the BUSY polarity, as the sample does at start
 *   z  wake path (Step 7): panel deep sleep, hardware reset, init and draw again
 *   d  ESP32 deep sleep with the panel asleep, for the current measurement (Step 6);
 *      press the reset button to come back
 *
 * Every draw logs the data transfer time and the refresh time (0x12 to BUSY release).
 * Record the results in firmware/bench/RESULTS.md. The pins are the plan's (settings.h). */
#include <Arduino.h>
#include <driver/gpio.h>
#include <driver/spi_master.h>
#include <esp_heap_caps.h>
#include <esp_sleep.h>

#include "test_frames.h"

static const int PIN_MOSI = D10, PIN_SCK = D8, PIN_CS = D1, PIN_DC = D2, PIN_RST = D3, PIN_BUSY = D4;
static const size_t FRAME_BYTES = 172800;
static const size_t CHUNK = 4092;
static const uint32_t CLOCKS[] = {2000000, 4000000, 8000000, 10000000};

static spi_device_handle_t spi;
static bool spi_ready = false;
static int clock_index = 0;
static bool batched = false;                 /* start as the sample does */
static bool busy_active_low = true;          /* the datasheet: L = busy */
static bool ignore_busy = false;
static uint8_t *frame;

static void spi_setup(void)
{
    if (spi_ready) spi_bus_remove_device(spi);
    else {
        spi_bus_config_t bus = {};
        bus.mosi_io_num = PIN_MOSI;
        bus.miso_io_num = -1;                /* D9 is the default MISO: keep it free for the MPU */
        bus.sclk_io_num = PIN_SCK;
        bus.quadwp_io_num = -1;
        bus.quadhd_io_num = -1;
        bus.max_transfer_sz = 4096;
        ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO));
    }
    spi_device_interface_config_t dev = {};
    dev.mode = 0;
    dev.clock_speed_hz = CLOCKS[clock_index];
    dev.spics_io_num = -1;
    dev.queue_size = 1;
    ESP_ERROR_CHECK(spi_bus_add_device(SPI2_HOST, &dev, &spi));
    spi_ready = true;
    Serial.printf("SPI %lu Hz, %s writes\n", (unsigned long)CLOCKS[clock_index], batched ? "batched" : "byte-at-a-time");
}

static void spi_send(const uint8_t *p, size_t n)
{
    while (n) {
        size_t k = n < CHUNK ? n : CHUNK;
        spi_transaction_t t = {};
        t.length = k * 8;
        t.tx_buffer = p;
        spi_device_polling_transmit(spi, &t);
        p += k;
        n -= k;
    }
}

static void command(uint8_t c)
{
    digitalWrite(PIN_DC, LOW);
    digitalWrite(PIN_CS, LOW);
    spi_send(&c, 1);
    digitalWrite(PIN_CS, HIGH);
}

static void data(const uint8_t *p, size_t n)
{
    digitalWrite(PIN_DC, HIGH);
    if (batched) {
        digitalWrite(PIN_CS, LOW);
        spi_send(p, n);
        digitalWrite(PIN_CS, HIGH);
    } else {
        for (size_t i = 0; i < n; i++) {     /* as the sample: CS around every byte */
            digitalWrite(PIN_CS, LOW);
            spi_send(p + i, 1);
            digitalWrite(PIN_CS, HIGH);
        }
    }
}

static void data1(uint8_t b) { data(&b, 1); }

static bool wait_busy(const char *stage, uint32_t timeout_ms)
{
    if (ignore_busy) return true;
    uint32_t t = millis();
    while (digitalRead(PIN_BUSY) == (busy_active_low ? LOW : HIGH)) {
        if (millis() - t > timeout_ms) {
            Serial.printf("  BUSY timeout at %s (pin=%d)\n", stage, digitalRead(PIN_BUSY));
            return false;
        }
        delay(1);
    }
    return true;
}

static void reset_panel(void)
{
    digitalWrite(PIN_RST, LOW);
    delay(20);
    digitalWrite(PIN_RST, HIGH);
    delay(20);
    wait_busy("reset", 15000);
    delay(10);
}

static void detect_busy_polarity(void)
{
    ignore_busy = false;
    if (wait_busy("polarity", 3000)) {
        Serial.printf("BUSY polarity ok, active %s\n", busy_active_low ? "low" : "high");
        return;
    }
    busy_active_low = !busy_active_low;
    if (wait_busy("polarity", 3000)) {
        Serial.printf("BUSY polarity switched: active %s\n", busy_active_low ? "low" : "high");
    } else {
        Serial.println("BUSY never idle: check the BUSY wire and panel power. Ignoring BUSY.");
        ignore_busy = true;
    }
}

static bool draw(const uint8_t *f)
{
    uint32_t t_all = millis();
    reset_panel();
    command(0xE9);
    data1(0x01);
    command(0x10);
    bool ok = wait_busy("DTM1", 15000);
    uint32_t t0 = millis();
    data(f, FRAME_BYTES);
    uint32_t transfer = millis() - t0;
    command(0x04);
    ok &= wait_busy("power on", 60000);
    delay(10);
    command(0x12);
    data1(0x00);
    t0 = millis();
    delay(10);
    ok &= wait_busy("refresh", 120000);
    uint32_t refresh = millis() - t0;
    command(0x02);
    data1(0x00);
    ok &= wait_busy("power off", 60000);
    delay(20);
    command(0x07);
    data1(0xA5);
    Serial.printf("  transfer %lu ms, refresh %lu ms, total %lu ms: %s\n", (unsigned long)transfer,
                  (unsigned long)refresh, (unsigned long)(millis() - t_all), ok ? "ok" : "BUSY TIMEOUT");
    return ok;
}

static void expand(const uint8_t *rle, size_t n)
{
    size_t o = 0;
    for (size_t i = 0; i + 1 < n && o < FRAME_BYTES; i += 2)
        for (uint8_t k = 0; k < rle[i] && o < FRAME_BYTES; k++) frame[o++] = rle[i + 1];
    if (o != FRAME_BYTES) Serial.printf("  frame expanded to %u bytes, expected %u\n", (unsigned)o, (unsigned)FRAME_BYTES);
}

static void solid(uint8_t b) { memset(frame, b, FRAME_BYTES); }

static void help(void)
{
    Serial.println("c corner  s swatch  w white  k black  m write mode  f SPI clock  p BUSY polarity"
                   "  z wake path  d ESP32 deep sleep");
}

void setup()
{
    Serial.begin(115200);
    uint32_t t = millis();
    while (!Serial && millis() - t < 3000) delay(10);
    gpio_hold_dis((gpio_num_t)PIN_CS);
    gpio_hold_dis((gpio_num_t)PIN_RST);
    pinMode(PIN_CS, OUTPUT);
    pinMode(PIN_DC, OUTPUT);
    pinMode(PIN_RST, OUTPUT);
    pinMode(PIN_BUSY, INPUT);
    digitalWrite(PIN_CS, HIGH);
    digitalWrite(PIN_DC, HIGH);
    digitalWrite(PIN_RST, HIGH);
    frame = (uint8_t *)heap_caps_malloc(FRAME_BYTES, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!frame) frame = (uint8_t *)malloc(FRAME_BYTES);
    Serial.printf("\nbench: frame buffer %s, BUSY pin now %d\n", frame ? "ok" : "FAILED", digitalRead(PIN_BUSY));
    spi_setup();
    delay(300);
    reset_panel();
    detect_busy_polarity();
    help();
}

void loop()
{
    if (!Serial.available() || !frame) return;
    char c = Serial.read();
    switch (c) {
    case 'c': Serial.println("corner test frame"); expand(corner_frame_rle, sizeof(corner_frame_rle)); draw(frame); break;
    case 's': Serial.println("swatch"); expand(swatch_frame_rle, sizeof(swatch_frame_rle)); draw(frame); break;
    case 'w': Serial.println("white"); solid(0x11); draw(frame); break;
    case 'k': Serial.println("black"); solid(0x00); draw(frame); break;
    case 'm': batched = !batched; spi_setup(); break;
    case 'f': clock_index = (clock_index + 1) % 4; spi_setup(); break;
    case 'p': reset_panel(); detect_busy_polarity(); break;
    case 'z':
        Serial.println("wake path: the panel is asleep after the last draw; reset and draw again");
        expand(corner_frame_rle, sizeof(corner_frame_rle));
        Serial.println(draw(frame) ? "  PASS: second draw after deep sleep" : "  FAIL: BUSY stuck after deep sleep");
        break;
    case 'd':
        Serial.println("ESP32 deep sleep now (panel asleep, RST and CS held high). Reset to return.");
        Serial.flush();
        digitalWrite(PIN_CS, HIGH);
        digitalWrite(PIN_RST, HIGH);
        gpio_hold_en((gpio_num_t)PIN_CS);
        gpio_hold_en((gpio_num_t)PIN_RST);
        gpio_deep_sleep_hold_en();
        esp_deep_sleep_start();
        break;
    case '\n': case '\r': break;
    default: help();
    }
}
