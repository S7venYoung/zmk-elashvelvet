/* SPDX-License-Identifier: MIT */
#include <zephyr/kernel.h>
#include <zephyr/sys/util.h>
#include <zmk/event_manager.h>
#include <zmk/events/position_state_changed.h>
#include <zmk/events/battery_state_changed.h>
#include "velvet_wpm.h"

static struct k_spinlock lock;
static struct velvet_history history[2];
static uint8_t batteries[2];
static uint8_t battery_valid;
static int positions(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *event=as_zmk_position_state_changed(eh);
    if(event && event->state) {
        int side=velvet_position_side(event->position);
        if(side>=0) {
            k_spinlock_key_t key=k_spin_lock(&lock);
            velvet_record(&history[side],k_uptime_get_32());
            k_spin_unlock(&lock,key);
        }
    }
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_fight_positions,positions);
ZMK_SUBSCRIPTION(velvet_fight_positions,zmk_position_state_changed);

static int battery(const zmk_event_t *eh) {
    const struct zmk_battery_state_changed *own=as_zmk_battery_state_changed(eh);
    const struct zmk_peripheral_battery_state_changed *remote=as_zmk_peripheral_battery_state_changed(eh);
    k_spinlock_key_t key=k_spin_lock(&lock);
    // Right is central; left is peripheral source0. Zero percent is valid.
    if(own) { batteries[1]=MIN(own->state_of_charge,100); battery_valid|=4; }
    if(remote && remote->source==0) { batteries[0]=MIN(remote->state_of_charge,100); battery_valid|=2; }
    k_spin_unlock(&lock,key);
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_fight_battery,battery);
ZMK_SUBSCRIPTION(velvet_fight_battery,zmk_battery_state_changed);
ZMK_SUBSCRIPTION(velvet_fight_battery,zmk_peripheral_battery_state_changed);

void fight_telemetry_read(uint8_t wpm[2], uint8_t battery[2], uint8_t *valid) {
    uint32_t now=k_uptime_get_32();
    k_spinlock_key_t key=k_spin_lock(&lock);
    for(int side=0;side<2;side++) {
        wpm[side]=velvet_wpm(&history[side],now);
        battery[side]=batteries[side];
    }
    *valid=1|battery_valid;
    k_spin_unlock(&lock,key);
}
