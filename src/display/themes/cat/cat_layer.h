/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define CAT_LAYER_EVENT "vlcat"
struct cat_layer_sample { uint32_t at; uint8_t layer; bool seen; };
static inline bool cat_layer_accept(struct cat_layer_sample *s, const uint8_t *p,
                                    size_t size, uint32_t now) {
    if (!p || size!=2 || p[0]!=1 || p[1]==255) return false;
    *s=(struct cat_layer_sample){.at=now,.layer=p[1],.seen=true};
    return true;
}
static inline bool cat_layer_live(const struct cat_layer_sample *s, uint32_t now) {
    return s->seen && (uint32_t)(now-s->at)<5000;
}
