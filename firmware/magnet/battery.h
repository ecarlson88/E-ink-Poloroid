/* Battery voltage (Task 6). */
#pragma once

/* Battery in millivolts: 16 samples of analogReadMilliVolts on D0 (factory-calibrated),
 * averaged, times the 2 x 1 MOhm divider ratio. Read before Wi-Fi starts (radio sag). */
int battery_read_mv(void);
