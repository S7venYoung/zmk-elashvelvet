/* SPDX-License-Identifier: MIT */
#include <zephyr/kernel.h>
#include <zephyr/irq.h>
#include <nrfx.h>
#include <zmk/event_manager.h>
#include <zmk/events/position_state_changed.h>
#include "eyelash_local_dfu.h"

static struct eyelash_dfu_hold hold;
static struct k_spinlock hold_lock;

static void enter_when_held(struct k_work *work) {
    ARG_UNUSED(work);
    k_spinlock_key_t key = k_spin_lock(&hold_lock);
    if (eyelash_dfu_due(&hold, k_uptime_get())) {
        /* Same request as the existing Pad DFU behavior. */
        NRF_POWER->GPREGRET = 0xA8;
        __DSB();
        NVIC_SystemReset();
    }
    k_spin_unlock(&hold_lock, key);
}
K_WORK_DELAYABLE_DEFINE(local_dfu_work, enter_when_held);

static int local_keys(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *ev = as_zmk_position_state_changed(eh);
    if (!ev || (ev->position != 61 && ev->position != 63)) {
        return ZMK_EV_EVENT_BUBBLE;
    }
    k_spinlock_key_t key = k_spin_lock(&hold_lock);
    int transition = eyelash_dfu_update(&hold, ev->position, ev->state, k_uptime_get());
    if (transition > 0) {
        k_work_reschedule(&local_dfu_work, K_MSEC(3000));
    } else if (transition < 0) {
        k_work_cancel_delayable(&local_dfu_work);
    }
    k_spin_unlock(&hold_lock, key);
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(eyelash_local_dfu, local_keys);
ZMK_SUBSCRIPTION(eyelash_local_dfu, zmk_position_state_changed);
