#include "qmk/effect_runner_sin_cos_i.h"
#include "qmk/effect_runner_i.h"
#include "qmk/effect_runner_dx_dy_dist.h"
#include "qmk/effect_runner_dx_dy.h"
#define ENABLE_RGB_MATRIX_BREATHING
#include "qmk/breathing_anim.h"
#define ENABLE_RGB_MATRIX_BAND_PINWHEEL_SAT
#include "qmk/colorband_pinwheel_sat_anim.h"
#define ENABLE_RGB_MATRIX_BAND_PINWHEEL_VAL
#include "qmk/colorband_pinwheel_val_anim.h"
#define ENABLE_RGB_MATRIX_BAND_SAT
#include "qmk/colorband_sat_anim.h"
#define ENABLE_RGB_MATRIX_BAND_SPIRAL_SAT
#include "qmk/colorband_spiral_sat_anim.h"
#define ENABLE_RGB_MATRIX_BAND_SPIRAL_VAL
#include "qmk/colorband_spiral_val_anim.h"
#define ENABLE_RGB_MATRIX_BAND_VAL
#include "qmk/colorband_val_anim.h"
#define ENABLE_RGB_MATRIX_CYCLE_ALL
#include "qmk/cycle_all_anim.h"
#define ENABLE_RGB_MATRIX_CYCLE_LEFT_RIGHT
#include "qmk/cycle_left_right_anim.h"
#define ENABLE_RGB_MATRIX_CYCLE_OUT_IN
#include "qmk/cycle_out_in_anim.h"
#define ENABLE_RGB_MATRIX_CYCLE_OUT_IN_DUAL
#include "qmk/cycle_out_in_dual_anim.h"
#define ENABLE_RGB_MATRIX_CYCLE_PINWHEEL
#include "qmk/cycle_pinwheel_anim.h"
#define ENABLE_RGB_MATRIX_CYCLE_SPIRAL
#include "qmk/cycle_spiral_anim.h"
#define ENABLE_RGB_MATRIX_CYCLE_UP_DOWN
#include "qmk/cycle_up_down_anim.h"
#define ENABLE_RGB_MATRIX_DUAL_BEACON
#include "qmk/dual_beacon_anim.h"
#define ENABLE_RGB_MATRIX_GRADIENT_LEFT_RIGHT
#include "qmk/gradient_left_right_anim.h"
#define ENABLE_RGB_MATRIX_GRADIENT_UP_DOWN
#include "qmk/gradient_up_down_anim.h"
#define ENABLE_RGB_MATRIX_HUE_BREATHING
#include "qmk/hue_breathing_anim.h"
#define ENABLE_RGB_MATRIX_HUE_PENDULUM
#include "qmk/hue_pendulum_anim.h"
#define ENABLE_RGB_MATRIX_HUE_WAVE
#include "qmk/hue_wave_anim.h"
#define ENABLE_RGB_MATRIX_RAINBOW_BEACON
#include "qmk/rainbow_beacon_anim.h"
#define ENABLE_RGB_MATRIX_RAINBOW_MOVING_CHEVRON
#include "qmk/rainbow_moving_chevron_anim.h"
#define ENABLE_RGB_MATRIX_RAINBOW_PINWHEELS
#include "qmk/rainbow_pinwheels_anim.h"

static bool (*const pad_effects[])(effect_params_t *) = {
    BREATHING,
    BAND_PINWHEEL_SAT,
    BAND_PINWHEEL_VAL,
    BAND_SAT,
    BAND_SPIRAL_SAT,
    BAND_SPIRAL_VAL,
    BAND_VAL,
    CYCLE_ALL,
    CYCLE_LEFT_RIGHT,
    CYCLE_OUT_IN,
    CYCLE_OUT_IN_DUAL,
    CYCLE_PINWHEEL,
    CYCLE_SPIRAL,
    CYCLE_UP_DOWN,
    DUAL_BEACON,
    GRADIENT_LEFT_RIGHT,
    GRADIENT_UP_DOWN,
    HUE_BREATHING,
    HUE_PENDULUM,
    HUE_WAVE,
    RAINBOW_BEACON,
    RAINBOW_MOVING_CHEVRON,
    RAINBOW_PINWHEELS,
};
