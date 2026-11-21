/* Host tests for firmware/main/logic.c. Plain C, no ESP-IDF.
 * Build and run from the repo root:
 *   gcc -Wall -Wextra -Werror firmware/test/test_logic.c firmware/main/logic.c -o /tmp/t && /tmp/t
 */
#include <stdio.h>

#include "../main/logic.h"

static int failures = 0;

#define CHECK(expr)                                                     \
    do {                                                                \
        if (!(expr)) {                                                  \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr);      \
            failures++;                                                 \
        }                                                               \
    } while (0)

/* Task 4: only a full 200 response may reach the panel. */
static void test_frame_ok(void)
{
    CHECK(frame_ok(200, 172800) == true);
    CHECK(frame_ok(200, 172799) == false);
    CHECK(frame_ok(200, 0) == false);
    CHECK(frame_ok(204, 0) == false);
    CHECK(frame_ok(401, 172800) == false);
    CHECK(frame_ok(500, 172800) == false);
}

/* Task 4: a day on success, FAIL_RETRY_SECONDS after a failure. */
static void test_next_sleep_seconds(void)
{
    CHECK(next_sleep_seconds(true, 0) == 86400);
    CHECK(next_sleep_seconds(false, 1) == FAIL_RETRY_SECONDS);
}

int main(void)
{
    test_frame_ok();
    test_next_sleep_seconds();
    if (failures) {
        printf("%d check(s) failed\n", failures);
        return 1;
    }
    printf("all logic tests passed\n");
    return 0;
}
