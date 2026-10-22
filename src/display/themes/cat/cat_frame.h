/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include "cat_art.h"

#define CAT_WIDTH 160
#define CAT_HEIGHT 68
#define CAT_FRAME_BYTES (CAT_WIDTH * CAT_HEIGHT / 8)
struct cat_status {
    bool connected, battery_valid, layer_valid;
    uint8_t battery, layer; /* layer is the zero-based ZMK layer index. */
};
static inline void cat_pixel(uint8_t *pixels, int x, int y, bool black) {
    if (x < 0 || x >= CAT_WIDTH || y < 0 || y >= CAT_HEIGHT) return;
    unsigned pos = (unsigned)y * CAT_WIDTH + (unsigned)x;
    uint8_t mask = 0x80u >> (pos & 7u);
    if (black) pixels[pos >> 3] |= mask;
    else pixels[pos >> 3] &= (uint8_t)~mask;
}
static inline void cat_rect(uint8_t *p, int x, int y, int w, int h, bool black) {
    for (int yy = y; yy < y+h; ++yy)
        for (int xx = x; xx < x+w; ++xx) cat_pixel(p, xx, yy, black);
}
static inline uint16_t cat_glyph(char c) {
    /* Compact 3x5 pixel lettering: top row in the most significant bits. */
    switch (c) {
    case '0': return 0x7b6f; case '1': return 0x2c97;
    case '2': return 0x73e7; case '3': return 0x73cf;
    case '4': return 0x5bc9; case '5': return 0x79cf;
    case '6': return 0x79ef; case '7': return 0x7249;
    case '8': return 0x7bef; case '9': return 0x7bcf;
    case 'B': return 0x6bae; case 'L': return 0x4927;
    case 'E': return 0x79a7; case 'A': return 0x2bed;
    case 'Y': return 0x5a92; case 'R': return 0x6bad;
    case '-': return 0x01c0; case '%': return 0x5295;
    default: return 0;
    }
}
static inline void cat_text(uint8_t *p, int x, int y, const char *text, int scale,
                            bool black) {
    for (; *text; ++text, x += 4*scale) {
        uint16_t bits = cat_glyph(*text);
        for (int row=0; row<5; ++row)
            for (int col=0; col<3; ++col)
                if (bits & (1u << (14-row*3-col)))
                    cat_rect(p,x+col*scale,y+row*scale,scale,scale,black);
    }
}
static inline void cat_label(uint8_t *p,int x,int y,const char *text,bool black) {
    for (;*text;++text,x+=6) {
        uint64_t bits=0;
        switch (*text) {
        case 'B': bits=UINT64_C(0x7a31f463e); break;
        case 'L': bits=UINT64_C(0x42108421f); break;
        case 'E': bits=UINT64_C(0x7e10f421f); break;
        case 'A': bits=UINT64_C(0x3a31fc631); break;
        case 'Y': bits=UINT64_C(0x462a21084); break;
        case 'R': bits=UINT64_C(0x7a31f5251); break;
        default: break;
        }
        for(int row=0;row<7;++row)
            for(int col=0;col<5;++col)
                if(bits & (UINT64_C(1)<<(34-row*5-col))) cat_pixel(p,x+col,y+row,black);
    }
}
static inline void cat_number(char out[5], unsigned value, bool percent) {
    unsigned i=0;
    if (value>=100) out[i++]=(char)('0'+value/100);
    if (value>=10) out[i++]=(char)('0'+value/10%10);
    out[i++]=(char)('0'+value%10);
    if (percent) out[i++]='%';
    out[i]=0;
}
static inline void cat_render(uint8_t p[CAT_FRAME_BYTES], struct cat_status s) {
    memset(p,0,CAT_FRAME_BYTES);
    /* Stepped monochrome border, divider and the reference-inspired kitten. */
    cat_rect(p,3,1,154,2,true); cat_rect(p,3,65,154,2,true);
    cat_rect(p,1,3,2,62,true); cat_rect(p,157,3,2,62,true);
    cat_rect(p,2,2,2,2,true); cat_rect(p,156,2,2,2,true);
    cat_rect(p,2,64,2,2,true); cat_rect(p,156,64,2,2,true);
    cat_rect(p,89,9,1,50,true);
    for (int y=0;y<CAT_ART_HEIGHT;++y)
        for (int x=0;x<CAT_ART_WIDTH;++x)
            if (cat_art[y*CAT_ART_STRIDE+x/8] & (128u>>(x%8)))
                cat_pixel(p,x+5,y+7,true);
    /* Battery outline and five proportional cells. Unknown is never 0%. */
    cat_rect(p,97,10,27,12,true); cat_rect(p,99,12,23,8,false);
    cat_rect(p,124,13,2,6,true);
    if (s.battery_valid)
        for (int n=0;n<5;++n)
            if (s.battery > n*20) cat_rect(p,100+n*4,13,3,6,true);
    char number[5];
    if (s.battery_valid) {
        cat_number(number,s.battery,true);
        cat_text(p,s.battery==100?129:131,13,number,s.battery==100?1:2,true);
    } else cat_text(p,133,14,"--",2,true);
    /* BLE rune; the three dots are one peer-link indicator, not host slots. */
    for (int y=28;y<42;++y) cat_pixel(p,100,y,true);
    for (int n=0;n<6;++n) {
        cat_pixel(p,100+n,28+n,true); cat_pixel(p,105-n,33+n,true);
        cat_pixel(p,100+n,35+n,true); cat_pixel(p,105-n,40+n,true);
        cat_pixel(p,96+n,31+n,true); cat_pixel(p,96+n,39-n,true);
    }
    cat_label(p,113,28,"BLE",true);
    for (int n=0;n<3;++n) {
        cat_rect(p,114+n*12,41,4,4,true);
        if (!s.connected) cat_rect(p,115+n*12,42,2,2,false);
    }
    /* Layer label uses a one-based number, so ZMK base layer 0 reads 1. */
    cat_rect(p,96,49,59,13,true); cat_rect(p,128,50,25,11,false);
    cat_label(p,98,52,"LAYER",false);
    if (s.layer_valid && s.connected) {
        unsigned value=(unsigned)s.layer+1;
        cat_number(number,value,false);
        unsigned digits=(unsigned)strlen(number);
        int scale=digits==1?2:1;
        cat_text(p,140-(int)(digits*4-1)*scale/2,51,number,scale,true);
    } else cat_text(p,137,53,"--",1,true);
}
