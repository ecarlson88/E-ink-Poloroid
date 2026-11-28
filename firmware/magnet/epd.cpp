/* Panel driver: see epd.h. Uses ESP-IDF's spi_master (part of the Arduino-ESP32 core), as
 * Good Display's sample does, with the same command sequence. Differences from the sample,
 * all to be confirmed on the bench (Task 1 Steps 5 to 7):
 *   - the frame data goes out in 4,092-byte transfers with CS held low, not one byte per
 *     CS pulse (Task 1 Step 5);
 *   - BUSY polarity is fixed by EPD_BUSY_ACTIVE_LOW instead of being guessed at run time;
 *   - RST and CS are held high through ESP32 deep sleep (epd_prepare_sleep). */
#include <Arduino.h>
#include <driver/gpio.h>
#include <driver/spi_master.h>

#include "epd.h"
#include "logic.h"
#include "settings.h"

static const uint32_t BUSY_TIMEOUT_INIT_MS = 15000;
static const uint32_t BUSY_TIMEOUT_POWER_MS = 60000;
static const uint32_t BUSY_TIMEOUT_REFRESH_MS = 120000;
static const size_t CHUNK = 4092;           /* bytes per SPI transfer (max_transfer_sz 4096) */

static spi_device_handle_t s_spi;
static bool s_ready = false;
static uint32_t s_refresh_ms = 0, s_transfer_ms = 0;

static bool epd_begin(void)
{
    if (s_ready) return true;
    /* Released from the deep-sleep hold set by epd_prepare_sleep. */
    gpio_hold_dis((gpio_num_t)PIN_EPD_CS);
    gpio_hold_dis((gpio_num_t)PIN_EPD_RST);

    pinMode(PIN_EPD_CS, OUTPUT);
    pinMode(PIN_EPD_DC, OUTPUT);
    pinMode(PIN_EPD_RST, OUTPUT);
    pinMode(PIN_EPD_BUSY, INPUT);
    digitalWrite(PIN_EPD_CS, HIGH);
    digitalWrite(PIN_EPD_DC, HIGH);
    digitalWrite(PIN_EPD_RST, HIGH);

    spi_bus_config_t bus = {};
    bus.mosi_io_num = PIN_EPD_MOSI;
    bus.miso_io_num = -1;                   /* D9 is the board's default MISO: leave it free */
    bus.sclk_io_num = PIN_EPD_SCK;
    bus.quadwp_io_num = -1;
    bus.quadhd_io_num = -1;
    bus.max_transfer_sz = 4096;

    spi_device_interface_config_t dev = {};
    dev.mode = 0;
    dev.clock_speed_hz = EPD_SPI_HZ;
    dev.spics_io_num = -1;                  /* CS driven by hand, as in the sample */
    dev.queue_size = 1;

    if (spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO) != ESP_OK) return false;
    if (spi_bus_add_device(SPI2_HOST, &dev, &s_spi) != ESP_OK) return false;
    s_ready = true;
    return true;
}

static void spi_send(const uint8_t *data, size_t len)
{
    while (len) {
        size_t n = len < CHUNK ? len : CHUNK;
        spi_transaction_t t = {};
        t.length = n * 8;
        t.tx_buffer = data;                 /* PSRAM buffers are copied to DMA memory by the driver */
        spi_device_polling_transmit(s_spi, &t);
        data += n;
        len -= n;
    }
}

static void write_command(uint8_t cmd)
{
    digitalWrite(PIN_EPD_DC, LOW);
    digitalWrite(PIN_EPD_CS, LOW);
    spi_send(&cmd, 1);
    digitalWrite(PIN_EPD_CS, HIGH);
}

static void write_data(const uint8_t *data, size_t len)
{
    digitalWrite(PIN_EPD_DC, HIGH);
    digitalWrite(PIN_EPD_CS, LOW);
    spi_send(data, len);
    digitalWrite(PIN_EPD_CS, HIGH);
}

static void write_byte(uint8_t b) { write_data(&b, 1); }

static bool wait_busy(const char *stage, uint32_t timeout_ms)
{
    const int busy_level = EPD_BUSY_ACTIVE_LOW ? LOW : HIGH;
    uint32_t start = millis();
    while (digitalRead(PIN_EPD_BUSY) == busy_level) {
        if (millis() - start > timeout_ms) {
            Serial.printf("[epd] BUSY timeout at %s\n", stage);
            return false;
        }
        delay(1);
    }
    return true;
}

static bool epd_reset(void)
{
    digitalWrite(PIN_EPD_RST, LOW);
    delay(20);
    digitalWrite(PIN_EPD_RST, HIGH);
    delay(20);
    bool ok = wait_busy("reset", BUSY_TIMEOUT_INIT_MS);
    delay(10);
    return ok;
}

bool epd_show_frame(const uint8_t *frame, size_t len)
{
    if (frame == NULL || len != FRAME_BYTES) return false;
    if (!epd_begin()) {
        Serial.println("[epd] SPI init failed");
        return false;
    }
    bool ok = epd_reset();

    write_command(0xE9);                    /* init, normal mode (the sample's default) */
    write_byte(0x01);

    write_command(0x10);                    /* frame data */
    ok &= wait_busy("DTM1", BUSY_TIMEOUT_INIT_MS);
    uint32_t t0 = millis();
    write_data(frame, len);
    s_transfer_ms = millis() - t0;

    write_command(0x04);                    /* power on */
    ok &= wait_busy("power on", BUSY_TIMEOUT_POWER_MS);
    delay(10);

    write_command(0x12);                    /* refresh */
    write_byte(0x00);
    t0 = millis();
    delay(10);
    ok &= wait_busy("refresh", BUSY_TIMEOUT_REFRESH_MS);
    s_refresh_ms = millis() - t0;

    write_command(0x02);                    /* power off */
    write_byte(0x00);
    ok &= wait_busy("power off", BUSY_TIMEOUT_POWER_MS);
    delay(20);

    write_command(0x07);                    /* panel deep sleep; only a hardware reset wakes it */
    write_byte(0xA5);

    Serial.printf("[epd] transfer %lu ms, refresh %lu ms, %s\n", (unsigned long)s_transfer_ms,
                  (unsigned long)s_refresh_ms, ok ? "ok" : "BUSY timeout");
    return ok;
}

void epd_prepare_sleep(void)
{
    /* Every sleep, also after a wake that never drew (a failed fetch): the lines must not float. */
    gpio_hold_dis((gpio_num_t)PIN_EPD_CS);
    gpio_hold_dis((gpio_num_t)PIN_EPD_RST);
    pinMode(PIN_EPD_CS, OUTPUT);
    pinMode(PIN_EPD_RST, OUTPUT);
    digitalWrite(PIN_EPD_CS, HIGH);
    digitalWrite(PIN_EPD_RST, HIGH);
    gpio_hold_en((gpio_num_t)PIN_EPD_CS);
    gpio_hold_en((gpio_num_t)PIN_EPD_RST);
    gpio_deep_sleep_hold_en();
}

uint32_t epd_last_refresh_ms(void) { return s_refresh_ms; }
uint32_t epd_last_transfer_ms(void) { return s_transfer_ms; }
