#include <Arduino.h>

#include "battery.h"
#include "settings.h"

int battery_read_mv(void)
{
    uint32_t sum = 0;
    for (int i = 0; i < 16; i++) sum += analogReadMilliVolts(PIN_BATTERY);
    return (int)(sum * BATTERY_DIVIDER / 16);
}
