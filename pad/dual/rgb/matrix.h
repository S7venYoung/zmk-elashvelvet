/* QMK RGB Matrix adapter for the 4x4 Pad. */
typedef struct { uint8_t h,s,v; } hsv_t;
typedef struct led_rgb rgb_t;
typedef struct { uint8_t x,y; } pad_point;
typedef struct { unsigned unused; } effect_params_t;
static const struct { pad_point point[16]; } g_led_config = {{
    {0,0},
    {75,0},
    {149,0},
    {224,0},
    {0,21},
    {75,21},
    {149,21},
    {224,21},
    {0,43},
    {75,43},
    {149,43},
    {224,43},
    {0,64},
    {75,64},
    {149,64},
    {224,64},
}};
static const pad_point k_rgb_matrix_center = {112,32};
static struct { hsv_t hsv; uint8_t speed; } rgb_matrix_config;
static uint16_t g_rgb_timer;
#define RGB_MATRIX_USE_LIMITS(lo,hi) uint8_t lo=0, hi=16
#define RGB_MATRIX_TEST_LED_FLAGS() ((void)0)
#define RGB_MATRIX_CUSTOM_EFFECT_IMPLS
#define RGB_MATRIX_EFFECT(name)
static inline bool rgb_matrix_check_finished_leds(unsigned count) { return count >= 16; }
static inline uint8_t scale8(uint8_t x,uint8_t s) { return ((uint16_t)x*(s+1u))>>8; }
static inline uint16_t scale16by8(uint16_t x,uint8_t s) { return ((uint32_t)x*(s+1u))>>8; }
static inline uint8_t qadd8(unsigned x,unsigned y) { return x+y>255?255:x+y; }
static inline uint8_t abs8(int8_t x) { return x<0?-x:x; }
static inline uint8_t sqrt16(uint16_t x) {
    unsigned root=0;
    for(unsigned bit=128;bit;bit>>=1) { unsigned n=root|bit; if(n*n<=x)root=n; }
    return root;
}
static inline uint8_t sin8(uint8_t t) {
    static const uint8_t quarter[65]={0,3,6,9,12,16,19,22,25,28,31,34,37,40,43,46,49,51,54,57,60,63,65,68,71,73,76,78,81,83,85,88,90,92,94,96,98,100,102,104,106,107,109,111,112,113,115,116,117,118,120,121,122,122,123,124,125,125,126,126,126,127,127,127,127};
    unsigned i=t&63;
    int v=quarter[t&64?64-i:i];
    return 128+(t&128?-v:v);
}
static inline uint8_t cos8(uint8_t t) { return sin8(t+64); }
static inline uint8_t atan2_8(int16_t y,int16_t x) {
    if (!y) return x<0?128:0;
    int a=abs(y);
    int angle=x>=0?32-32*(x-a)/(x+a):96-32*(x+a)/(a-x);
    return y<0?-angle:angle;
}
static rgb_t rgb_matrix_hsv_to_rgb(hsv_t c) {
    return hsb_to_rgb(hsb_scale_zero_max((struct zmk_led_hsb){
        .h=c.h*360u/256,.s=c.s*100u/255,.b=c.v*100u/255}));
}
static void rgb_matrix_set_color(unsigned i,uint8_t r,uint8_t g,uint8_t b) {
    pixels[i]=(rgb_t){.r=r,.g=g,.b=b};
}
#include "effects.h"
BUILD_ASSERT(STRIP_NUM_PIXELS==16 && ARRAY_SIZE(pad_effects)==PAD_MATRIX_EFFECTS);
static void pad_matrix_tick(unsigned index) {
    if(index>=ARRAY_SIZE(pad_effects))return;
    rgb_matrix_config.hsv=(hsv_t){state.color.h*256u/360,state.color.s*255u/100,state.color.b*255u/100};
    rgb_matrix_config.speed=state.animation_speed*48u;
    g_rgb_timer=k_uptime_get_32();
    effect_params_t params={0};
    pad_effects[index](&params);
}
