/* SPDX-License-Identifier: MIT */
#pragma once
#include "cat_frame.h"
#define CAT_L8_BYTES (CAT_WIDTH * CAT_HEIGHT)
/* Native grayscale avoids indexed-image palette decoding during repaint. */
static inline void cat_expand_l8(const uint8_t packed[CAT_FRAME_BYTES],
                                 uint8_t pixels[CAT_L8_BYTES]) {
    for (unsigned i=0;i<CAT_L8_BYTES;++i)
        pixels[i]=(packed[i/8] & (0x80u>>(i%8)))?0:255;
}
