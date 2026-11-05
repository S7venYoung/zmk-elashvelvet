/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "../common/wait_screen.h"

static unsigned bits(const uint8_t *pixels) {
    unsigned count = 0;
    for (unsigned i = 0; i < PANEL_BYTES; i++) {
        count += __builtin_popcount(pixels[i]);
    }
    return count;
}

int main(void) {
    struct {
        uint8_t before[16];
        uint8_t pixels[PANEL_BYTES];
        uint8_t after[16];
    } frame;

    memset(&frame, 0xa5, sizeof(frame));
    dashboard_render_wait(frame.pixels, false);
    assert(bits(frame.pixels) > 0);
    assert(bits(frame.pixels) < PANEL_W * PANEL_H);
    for (unsigned i = 0; i < sizeof(frame.before); i++) {
        assert(frame.before[i] == 0xa5);
        assert(frame.after[i] == 0xa5);
    }

    uint8_t disconnected[PANEL_BYTES];
    memcpy(disconnected, frame.pixels, sizeof(disconnected));
    dashboard_render_wait(frame.pixels, true);
    assert(bits(frame.pixels) > 0);
    assert(memcmp(disconnected, frame.pixels, sizeof(disconnected)) != 0);
    return 0;
}
