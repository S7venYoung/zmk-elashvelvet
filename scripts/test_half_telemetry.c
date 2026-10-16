/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdint.h>
#include "half_telemetry.h"
int main(void) {
    struct velvet_half_sample samples[2] = {0};
    uint8_t right[] = {1, 1, 42, 75, 1};
    uint8_t left[] = {1, 0, 31, 0, 1};
    /* Connection order is deliberately right first; zero battery is valid. */
    assert(velvet_half_accept(samples, right, sizeof(right), 100));
    assert(velvet_half_accept(samples, left, sizeof(left), 200));
    assert(samples[0].battery == 0 && samples[0].battery_valid);
    assert(samples[1].battery == 75 && samples[1].battery_valid);
    assert(velvet_half_wpm(&samples[0], 201) == 31);
    assert(velvet_half_wpm(&samples[1], 201) == 42);
    assert(velvet_half_wpm(&samples[0], 5200) == 0);
    uint8_t no_battery[] = {1, 0, 10, 255, 0};
    assert(velvet_half_accept(samples, no_battery, 5, 400));
    assert(samples[0].battery_valid && samples[0].battery == 0);
    assert(!velvet_half_accept(samples, left, 4, 500));
    left[0] = 2; assert(!velvet_half_accept(samples, left, 5, 500));
    left[0] = 1; left[1] = 2; assert(!velvet_half_accept(samples, left, 5, 500));
    left[1] = 0; left[3] = 101; assert(!velvet_half_accept(samples, left, 5, 500));
    left[3] = 40; left[4] = 2; assert(!velvet_half_accept(samples, left, 5, 500));
    left[4] = 1; assert(velvet_half_accept(samples, left, 5, UINT32_MAX - 100));
    assert(velvet_half_wpm(&samples[0], 100) == 31);
    return 0;
}
