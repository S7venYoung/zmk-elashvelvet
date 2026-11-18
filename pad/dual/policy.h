/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "layout.h"
static inline uint32_t pad_crc32(const uint8_t *p, size_t len) {
    uint32_t crc = UINT32_MAX;
    while (len--) {
        crc ^= *p++;
        for (unsigned n = 0; n < 8; n++) crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}
static inline bool pad_mode_record_valid(uint32_t a, uint32_t b) {
    return (a == PAD_MODE_MAGIC || a == (PAD_MODE_MAGIC | 1u)) && b == ~a;
}
static inline unsigned pad_read_mode(const volatile uint32_t *words, size_t count) {
    unsigned mode = 0;
    for (size_t i = 0; i + 1 < count; i += 2) {
        if (pad_mode_record_valid(words[i], words[i + 1])) mode = words[i] & 1u;
    }
    return mode;
}
static inline bool pad_vector_valid(uint32_t sp, uint32_t pc, uint32_t base, uint32_t end) {
    return sp > 0x20000000u && sp <= 0x20040000u && !(sp & 7u) &&
           (pc & 1u) && (pc & ~1u) >= base && (pc & ~1u) < end;
}
struct pad_image_descriptor { uint32_t mode, base, length, crc; };
struct pad_image_table { uint32_t magic, version, count, reserved; struct pad_image_descriptor image[2]; };
struct pad_chord_state { uint32_t held; bool swallowed, armed, pending; int64_t started; };
static inline bool pad_chord_event(struct pad_chord_state *s, unsigned position,
                                  bool pressed, int64_t now, bool *switch_now) {
    const uint32_t fn = 1u << 12, mode = 1u << 10;
    bool consume = position == 10 && s->swallowed;
    *switch_now = false;
    if (pressed) s->held |= 1u << position;
    else s->held &= ~(1u << position);
    if (pressed && position == 10 && s->held == (fn | mode)) {
        s->swallowed = s->armed = true; s->started = now; consume = true;
    }
    if (s->held & ~(fn | mode)) s->armed = s->pending = false;
    if (!pressed && (position == 10 || position == 12) && s->armed) {
        s->pending = now - s->started >= 2000; s->armed = false;
    }
    if (!pressed && position == 10) s->swallowed = false;
    if (!s->held && s->pending) { *switch_now = true; s->pending = false; }
    return consume;
}
