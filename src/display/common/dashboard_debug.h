/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#define DASH_ACK_EVENT "vldack"
#define DASH_ACK_SIZE 12
#define DASH_DEBUG_SIZE 52
static inline void dash_debug_put32(uint8_t *p, uint32_t value) {
    for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(value>>(8*i));
}
static inline uint32_t dash_debug_u32(const uint8_t *p) {
    return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
static inline void dash_ack_encode(uint8_t *p, unsigned side, unsigned theme,
                                   bool connected, bool fresh, uint32_t received,
                                   uint32_t drawn) {
    p[0]=1;p[1]=side;p[2]=theme;p[3]=(connected?1:0)|(fresh?2:0);
    dash_debug_put32(p+4,received);dash_debug_put32(p+8,drawn);
}
static inline bool dash_ack_valid(const uint8_t *p, unsigned size) {
    return p&&size==DASH_ACK_SIZE&&p[0]==1&&p[1]<2&&p[2]<2&&!(p[3]&~3u);
}
