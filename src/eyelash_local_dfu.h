/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdbool.h>
#include <stdint.h>
struct eyelash_dfu_hold { unsigned mask; int64_t since; };
static inline int eyelash_dfu_update(struct eyelash_dfu_hold *s, unsigned position,
                                     bool pressed, int64_t now) {
    unsigned bit = position == 61 ? 1u : position == 63 ? 2u : 0u;
    unsigned old = s->mask;
    s->mask = pressed ? old | bit : old & ~bit;
    if (old != 3 && s->mask == 3) { s->since = now; return 1; }
    if (old == 3 && s->mask != 3) { return -1; }
    return 0;
}
static inline bool eyelash_dfu_due(const struct eyelash_dfu_hold *s, int64_t now) {
    return s->mask == 3 && now - s->since >= 3000;
}
