/* SPDX-License-Identifier: MIT */
#include <string.h>
#include <zephyr/sys/util.h>
#include <zmk/hid.h>
#include "fight_status.h"
#include "scanner_payload.h"

static uint8_t frame[17] = {0xff, 0xff, 0xab, 0xce, 1};
static uint16_t sequence;
static unsigned int cycle;

const uint8_t *velvet_scanner_payload(const uint8_t *status, size_t status_size,
                                     const uint8_t keyboard_id[4], size_t *size) {
    /* Alternate status and per-half telemetry so Cube input does not expire. */
    if (++cycle % 2 != 0) {
        *size = status_size;
        return status;
    }
    uint8_t wpm[2], battery[2], valid;
    fight_telemetry_read(wpm, battery, &valid);
    frame[5] = valid;
    memcpy(frame + 6, keyboard_id, 4);
    frame[10] = wpm[0];
    frame[11] = wpm[1];
    frame[12] = battery[0];
    frame[13] = battery[1];
    struct zmk_hid_keyboard_report *report = zmk_hid_get_keyboard_report();
    frame[14] = report ? report->body.modifiers : 0;
    frame[15] = (uint8_t)sequence;
    frame[16] = (uint8_t)(sequence++ >> 8);
    *size = sizeof(frame);
    return frame;
}
