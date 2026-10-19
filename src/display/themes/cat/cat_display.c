/* SPDX-License-Identifier: MIT */
#include <string.h>
#include <lvgl.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/split/bluetooth/peripheral.h>
#include "cat_frame.h"
#include "cat_layer.h"
#include "cat_l8.h"

/* Keep both buffers static. L8 is consumed directly by LVGL's software
 * renderer, without an indexed palette or an indexed decoder line buffer. */
static uint8_t frame_bits[CAT_FRAME_BYTES];
static uint8_t image_bytes[CAT_L8_BYTES] __aligned(4);
static const lv_image_dsc_t image_source = {
    .header={.magic=LV_IMAGE_HEADER_MAGIC,.cf=LV_COLOR_FORMAT_L8,
             .flags=LV_IMAGE_FLAGS_MODIFIABLE,.w=CAT_WIDTH,.h=CAT_HEIGHT,
             .stride=CAT_WIDTH},
    .data_size=sizeof(image_bytes),.data=image_bytes,
};
static lv_obj_t *image;
static struct cat_status previous;
static bool drawn;
static atomic_t battery_value=ATOMIC_INIT(101); /* Unknown until a real sample. */
static struct cat_layer_sample layer_sample;
static struct k_spinlock layer_lock;

static int receive_battery(const zmk_event_t *eh) {
    const struct zmk_battery_state_changed *ev=as_zmk_battery_state_changed(eh);
    if (ev && ev->state_of_charge<=100) atomic_set(&battery_value,ev->state_of_charge);
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_cat_battery,receive_battery);
ZMK_SUBSCRIPTION(velvet_cat_battery,zmk_battery_state_changed);

static int receive_layer(const zmk_event_t *eh) {
    const struct zmk_relay_event_received *ev=as_zmk_relay_event_received(eh);
    if (!ev || !ev->event_name || strcmp(ev->event_name,CAT_LAYER_EVENT))
        return ZMK_EV_EVENT_BUBBLE;
    k_spinlock_key_t key=k_spin_lock(&layer_lock);
    bool accepted=cat_layer_accept(&layer_sample,ev->event_data,ev->event_data_size,
                                   k_uptime_get_32());
    k_spin_unlock(&layer_lock,key);
    return accepted?ZMK_EV_EVENT_HANDLED:ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_cat_layer,receive_layer);
ZMK_SUBSCRIPTION(velvet_cat_layer,zmk_relay_event_received);

/* Called only by the display queue: event callbacks never invoke LVGL. */
static void refresh(lv_timer_t *timer) {
    ARG_UNUSED(timer);
    uint8_t battery=(uint8_t)atomic_get(&battery_value);
    struct cat_status current={
        .connected=zmk_split_bt_peripheral_is_connected(),
        .battery_valid=battery<=100,.battery=battery,
    };
    k_spinlock_key_t key=k_spin_lock(&layer_lock);
    current.layer=layer_sample.layer;
    current.layer_valid=cat_layer_live(&layer_sample,k_uptime_get_32());
    k_spin_unlock(&layer_lock,key);
    if (drawn && current.connected==previous.connected &&
        current.battery_valid==previous.battery_valid && current.battery==previous.battery &&
        current.layer_valid==previous.layer_valid && current.layer==previous.layer) return;
    cat_render(frame_bits,current);
    cat_expand_l8(frame_bits,image_bytes);
    previous=current;
    drawn=true;
    lv_obj_invalidate(image);
}

lv_obj_t *zmk_display_status_screen(void) {
    lv_obj_t *screen=lv_obj_create(NULL);
    lv_obj_set_style_bg_color(screen,lv_color_white(),0);
    lv_obj_set_style_bg_opa(screen,LV_OPA_COVER,0);
    lv_obj_set_style_pad_all(screen,0,0);
    lv_obj_set_style_border_width(screen,0,0);
    lv_obj_remove_flag(screen,LV_OBJ_FLAG_SCROLLABLE);
    image=lv_image_create(screen);
    lv_image_set_src(image,&image_source);
    lv_obj_set_pos(image,0,0);
    refresh(NULL);
    lv_timer_create(refresh,250,NULL);
    return screen;
}
