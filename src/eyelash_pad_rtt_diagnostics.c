// SPDX-License-Identifier: MIT
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zmk/event_manager.h>
#include <zmk/events/position_state_changed.h>

LOG_MODULE_REGISTER(eyelash_pad_rtt, LOG_LEVEL_INF);

void eyelash_pad_rtt_trace(const char *event, int result, int state) {
    LOG_INF("PAD_RTT %s result=%d state=%d", event, result, state);
}

static int trace_key(const zmk_event_t *event) {
    const struct zmk_position_state_changed *position = as_zmk_position_state_changed(event);
    if (position && position->state) {
        LOG_INF("PAD_RTT key_down");
    }
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(eyelash_pad_rtt_key, trace_key);
ZMK_SUBSCRIPTION(eyelash_pad_rtt_key, zmk_position_state_changed);

static void heartbeat(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(pad_rtt_heartbeat, heartbeat);

static void heartbeat(struct k_work *work) {
    ARG_UNUSED(work);
    LOG_INF("PAD_RTT heartbeat");
    k_work_schedule(&pad_rtt_heartbeat, K_SECONDS(10));
}

static int init_pad_trace(void) {
    LOG_INF("PAD_RTT boot");
    k_work_schedule(&pad_rtt_heartbeat, K_SECONDS(10));
    return 0;
}
SYS_INIT(init_pad_trace, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
