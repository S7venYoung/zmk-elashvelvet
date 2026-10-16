/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define VELVET_HALF_EVENT "vlthalf"
#define VELVET_HALF_PACKET_SIZE 5
struct velvet_half_sample {
    uint32_t received_at;
    uint8_t wpm, battery;
    bool seen, battery_valid;
};
static inline bool velvet_half_accept(struct velvet_half_sample samples[2],
                                     const uint8_t *data, size_t size, uint32_t now) {
    if (!data || size != VELVET_HALF_PACKET_SIZE || data[0] != 1 || data[1] > 1 ||
        (data[4] & ~1u) || ((data[4] & 1u) && data[3] > 100)) {
        return false;
    }
    struct velvet_half_sample *sample = &samples[data[1]];
    sample->received_at = now;
    sample->wpm = data[2];
    sample->seen = true;
    if (data[4] & 1u) {
        sample->battery = data[3];
        sample->battery_valid = true;
    }
    return true;
}
static inline uint8_t velvet_half_wpm(const struct velvet_half_sample *sample, uint32_t now) {
    return sample->seen && (uint32_t)(now - sample->received_at) < 5000 ? sample->wpm : 0;
}
void velvet_half_read(uint8_t wpm[2], uint8_t battery[2], uint8_t *battery_valid,
                      uint8_t *seen);
