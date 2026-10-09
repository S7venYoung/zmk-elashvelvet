#pragma once
#include <stdint.h>
#include <stdbool.h>

// Logical positions from velvet.dtsi default_transform, not raw matrix columns.
static inline int velvet_position_side(uint32_t position) {
    if (position >= 61) return -1;
    return position < 6 || (position >= 12 && position < 19) ||
        (position >= 25 && position < 32) || (position >= 38 && position < 45) ||
        (position >= 51 && position < 56) ? 0 : 1;
}
struct velvet_history { uint32_t times[128]; uint8_t head; uint8_t count; };
static inline void velvet_record(struct velvet_history *h, uint32_t now) {
    h->times[h->head]=now; h->head=(h->head+1u)%128u;
    if(h->count<128) h->count++;
}
static inline uint8_t velvet_wpm(const struct velvet_history *h, uint32_t now) {
    uint32_t count=0;
    for(uint32_t i=0;i<h->count;i++) {
        uint32_t index=(h->head+127u-i)%128u;
        if((uint32_t)(now-h->times[index])>5000u) break;
        count++;
    }
    uint32_t wpm=(count*12u+2u)/5u;
    return wpm>255u ? 255u : (uint8_t)wpm;
}
