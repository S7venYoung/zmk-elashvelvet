/* SPDX-License-Identifier: MIT */
#pragma once

#include "pixels.h"

/* A visible fallback is safer than an all-white memory-LCD frame while the
 * receiver is reconnecting or the first dashboard theme packet is pending. */
static inline void dashboard_render_wait(uint8_t *p, bool connected) {
    memset(p, 0xff, PANEL_BYTES);

    const char *status = connected ? "SPLIT OK" : "NO SPLIT";
    const char *hint = connected ? "WAIT THEME" : "CHECK POWER";
    int status_scale = 2;
    int status_x = (PANEL_W - (int)strlen(status) * 6 * status_scale) / 2;
    int hint_x = (PANEL_W - (int)strlen(hint) * 6) / 2;

    text(p, status_x, 17, status, status_scale);
    text(p, hint_x, 41, hint, 1);

    /* Fixed rails make a failed/partial panel update visually distinct from a
     * blank or uniformly white frame. */
    box(p, 8, 4, PANEL_W - 16, 1, false);
    box(p, 8, PANEL_H - 5, PANEL_W - 16, 1, false);
}
