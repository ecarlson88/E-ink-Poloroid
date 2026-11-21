#include "logic.h"

bool frame_ok(int http_status, size_t len)
{
    return http_status == 200 && len == FRAME_BYTES;
}

uint32_t next_sleep_seconds(bool success, int consecutive_failures)
{
    /* The failure count is not used yet: Task 5 sends the device to setup
     * mode on the third failure, before this is called. */
    (void)consecutive_failures;
    return success ? DAILY_SLEEP_SECONDS : FAIL_RETRY_SECONDS;
}
