/* SPDX-License-Identifier: MIT */
#include <string.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zmk/event_manager.h>
#include "half_telemetry.h"

#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
static struct k_spinlock half_lock;
static struct velvet_half_sample samples[2];

static int receive_half(const zmk_event_t *eh) {
    const struct zmk_relay_event_received *event = as_zmk_relay_event_received(eh);
    if (!event || !event->event_name || strcmp(event->event_name, VELVET_HALF_EVENT)) {
        return ZMK_EV_EVENT_BUBBLE;
    }
    k_spinlock_key_t key = k_spin_lock(&half_lock);
    bool accepted = velvet_half_accept(samples, event->event_data, event->event_data_size,
                                       k_uptime_get_32());
    k_spin_unlock(&half_lock, key);
    return accepted ? ZMK_EV_EVENT_HANDLED : ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_half_receiver, receive_half);
ZMK_SUBSCRIPTION(velvet_half_receiver, zmk_relay_event_received);

void velvet_half_read(uint8_t wpm[2], uint8_t battery[2], uint8_t *valid, uint8_t *seen) {
    uint32_t now = k_uptime_get_32();
    *valid = *seen = 0;
    k_spinlock_key_t key = k_spin_lock(&half_lock);
    for (int side = 0; side < 2; side++) {
        wpm[side] = velvet_half_wpm(&samples[side], now);
        battery[side] = samples[side].battery;
        if (samples[side].seen) *seen |= (1u << side);
        if (samples[side].battery_valid) *valid |= (1u << (side + 1));
    }
    k_spin_unlock(&half_lock, key);
}
#else
#include <zmk/battery.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/position_state_changed.h>
#include <zmk/split/peripheral.h>
#include "velvet_wpm.h"

#if IS_ENABLED(CONFIG_SHIELD_VELVET_LEFT)
#define PHYSICAL_SIDE 0
#elif IS_ENABLED(CONFIG_SHIELD_VELVET_RIGHT)
#define PHYSICAL_SIDE 1
#else
#error "Half telemetry requires a physical left/right keyboard shield"
#endif

static struct k_spinlock half_lock;
static struct velvet_history local_history;
static bool battery_seen;
static uint8_t local_battery;

static int local_key(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *event = as_zmk_position_state_changed(eh);
    if (event && event->state && event->source == ZMK_POSITION_STATE_CHANGE_SOURCE_LOCAL) {
        k_spinlock_key_t key = k_spin_lock(&half_lock);
        velvet_record(&local_history, k_uptime_get_32());
        k_spin_unlock(&half_lock, key);
    }
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_half_keys, local_key);
ZMK_SUBSCRIPTION(velvet_half_keys, zmk_position_state_changed);

static int local_battery_changed(const zmk_event_t *eh) {
    const struct zmk_battery_state_changed *event = as_zmk_battery_state_changed(eh);
    if (event && event->state_of_charge <= 100) {
        k_spinlock_key_t key = k_spin_lock(&half_lock);
        local_battery = event->state_of_charge;
        battery_seen = true;
        k_spin_unlock(&half_lock, key);
    }
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_half_battery, local_battery_changed);
ZMK_SUBSCRIPTION(velvet_half_battery, zmk_battery_state_changed);

static void publish_half(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(half_publish_work, publish_half);
static void publish_half(struct k_work *work) {
    ARG_UNUSED(work);
    struct zmk_split_transport_peripheral_event event = {
        .type = ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_RELAY_EVENT,
        .data.relay_event.header.event_data_size = VELVET_HALF_PACKET_SIZE,
    };
    strcpy(event.data.relay_event.event_type, VELVET_HALF_EVENT);
    uint8_t *data = event.data.relay_event.event_data;
    data[0] = 1;
    data[1] = PHYSICAL_SIDE;
    k_spinlock_key_t key = k_spin_lock(&half_lock);
    data[2] = velvet_wpm(&local_history, k_uptime_get_32());
    data[3] = local_battery;
    data[4] = battery_seen ? 1 : 0;
    k_spin_unlock(&half_lock, key);
    /* Report over the existing split relay; never create a BLE advertiser. */
    (void)zmk_split_peripheral_report_event(&event);
    k_work_reschedule(&half_publish_work, K_SECONDS(1));
}

static int init_half(void) {
    k_work_schedule(&half_publish_work, K_SECONDS(3));
    return 0;
}
SYS_INIT(init_half, APPLICATION, 90);
#endif
