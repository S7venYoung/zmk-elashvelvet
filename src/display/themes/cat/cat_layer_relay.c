/* SPDX-License-Identifier: MIT */
#include <string.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zmk/event_manager.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/keymap.h>
#include <zmk/split/central.h>
#include "cat_layer.h"

static void publish_layer(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(cat_layer_work,publish_layer);
static void publish_layer(struct k_work *work) {
    ARG_UNUSED(work);
    struct zmk_split_relay_event_payload payload={.header.event_type_size=sizeof(CAT_LAYER_EVENT)-1,
 .header.event_data_size=2};
    strcpy(payload.event_type,CAT_LAYER_EVENT);
    payload.event_data[0]=1;
    payload.event_data[1]=zmk_keymap_highest_layer_active();
    /* Existing split transport broadcasts a tiny snapshot to connected halves. */
    (void)zmk_split_central_send_relay_event(&payload);
    k_work_reschedule(&cat_layer_work,K_SECONDS(1));
}
static int layer_changed(const zmk_event_t *eh) {
    ARG_UNUSED(eh);
    k_work_reschedule(&cat_layer_work,K_MSEC(50));
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_cat_layer_sender,layer_changed);
ZMK_SUBSCRIPTION(velvet_cat_layer_sender,zmk_layer_state_changed);
static int init_layer_relay(void) {
    k_work_schedule(&cat_layer_work,K_SECONDS(3));
    return 0;
}
SYS_INIT(init_layer_relay,APPLICATION,90);
