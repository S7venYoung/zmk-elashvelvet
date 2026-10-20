/* SPDX-License-Identifier: MIT */
#include <lvgl.h>
#include <zephyr/kernel.h>
#include <zephyr/init.h>
#include <zephyr/settings/settings.h>
#include <zephyr/sys/atomic.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/split/bluetooth/peripheral.h>
#include "themes/cat/cat_frame.h"
#include "themes/cat/cat_l8.h"
#include "themes/cat/cat_layer.h"
#include "common/dashboard_debug.h"
#include <zmk/split/peripheral.h>
#include "themes/codex-system/left/render.h"
#include "themes/codex-system/right/render.h"

BUILD_ASSERT(sizeof(DASH_EVENT)-1 <= CONFIG_ZMK_SPLIT_RELAY_EVENT_TYPE_NAME_LEN,
             "DASH_EVENT exceeds split relay event-name capacity");
BUILD_ASSERT(sizeof(DASH_ACK_EVENT)-1 <= CONFIG_ZMK_SPLIT_RELAY_EVENT_TYPE_NAME_LEN,
             "DASH_ACK_EVENT exceeds split relay event-name capacity");
BUILD_ASSERT(sizeof(CAT_LAYER_EVENT)-1 <= CONFIG_ZMK_SPLIT_RELAY_EVENT_TYPE_NAME_LEN,
             "CAT_LAYER_EVENT exceeds split relay event-name capacity");

static uint8_t packed[PANEL_BYTES],gray[CAT_L8_BYTES] __aligned(4);
static const lv_image_dsc_t source={.header={.magic=LV_IMAGE_HEADER_MAGIC,
 .cf=LV_COLOR_FORMAT_L8,.flags=LV_IMAGE_FLAGS_MODIFIABLE,.w=PANEL_W,.h=PANEL_H,.stride=PANEL_W},
 .data_size=sizeof(gray),.data=gray};
static lv_obj_t *image;
static atomic_t battery=ATOMIC_INIT(101);
static struct k_spinlock lock;
static uint8_t host[DASH_DATA_SIZE],theme=0,output=DASH_OUTPUT_NONE,profile;
static bool received,theme_known;
static atomic_t received_count,drawn_count;
static uint32_t received_at;
static struct cat_layer_sample layer;
static struct dashboard_status view;
static uint8_t history_sequence;
static bool history_started;

/* Only the theme is durable; live telemetry must never be written to flash. */
static uint8_t saved_theme=UINT8_MAX;
static void save_theme(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(theme_save_work,save_theme);
static void save_theme(struct k_work *work){
 ARG_UNUSED(work);
 k_spinlock_key_t key=k_spin_lock(&lock);
 uint8_t selected=theme;
 bool dirty=theme_known&&selected!=saved_theme;
 k_spin_unlock(&lock,key);
 if(!dirty)return;
 int rc=settings_save_one("velvet_panel/theme",&selected,sizeof(selected));
 key=k_spin_lock(&lock);
 if(rc==0)saved_theme=selected;
 bool changed=rc==0&&theme!=saved_theme;
 k_spin_unlock(&lock,key);
 if(changed)k_work_reschedule(&theme_save_work,K_MSEC(CONFIG_ZMK_SETTINGS_SAVE_DEBOUNCE));
}
static int load_theme(const char *name,size_t len,settings_read_cb read_cb,void *arg){
 const char *next;
 if(!settings_name_steq(name,"theme",&next)||next)return -ENOENT;
 if(len!=sizeof(uint8_t))return -EINVAL;
 uint8_t selected;
 int rc=read_cb(arg,&selected,sizeof(selected));
 if(rc<0)return rc;
 if(rc!=sizeof(selected)||selected>1)return -EINVAL;
 k_spinlock_key_t key=k_spin_lock(&lock);
 /* settings_load runs before the first display frame. */
 if(!received){theme=selected;theme_known=true;}
 saved_theme=selected;
 k_spin_unlock(&lock,key);
 return 0;
}
SETTINGS_STATIC_HANDLER_DEFINE(velvet_panel,"velvet_panel",NULL,load_theme,NULL,NULL);

static int on_event(const zmk_event_t *eh){
 const struct zmk_battery_state_changed *b=as_zmk_battery_state_changed(eh);
 if(b&&b->state_of_charge<=100)atomic_set(&battery,b->state_of_charge);
 const struct zmk_relay_event_received *e=as_zmk_relay_event_received(eh);
 if(!e||!e->event_name)return ZMK_EV_EVENT_BUBBLE;
 bool handled=false,cache_dirty=false;k_spinlock_key_t key=k_spin_lock(&lock);
 if(!strcmp(e->event_name,CAT_LAYER_EVENT))
  handled=cat_layer_accept(&layer,e->event_data,e->event_data_size,k_uptime_get_32());
 else if(!strcmp(e->event_name,DASH_EVENT)&&e->event_data_size==DASH_PACKET_SIZE){
  const uint8_t *p=e->event_data;
  if(dash_theme_packet_valid(p,e->event_data_size)){
   theme=p[1];theme_known=true;cache_dirty=theme!=saved_theme;output=p[2];profile=p[3];
   memcpy(host,p+DASH_PACKET_HEADER_SIZE,sizeof(host));
   received=true;received_at=k_uptime_get_32();handled=true;
   atomic_inc(&received_count);
  }
 }
 k_spin_unlock(&lock,key);
 /* Do not reset the debounce on each one-second telemetry packet. */
 if(cache_dirty)k_work_schedule(&theme_save_work,K_MSEC(CONFIG_ZMK_SETTINGS_SAVE_DEBOUNCE));
 return handled?ZMK_EV_EVENT_HANDLED:ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_dashboard,on_event);
ZMK_SUBSCRIPTION(velvet_dashboard,zmk_battery_state_changed);
ZMK_SUBSCRIPTION(velvet_dashboard,zmk_relay_event_received);

static void refresh(lv_timer_t *timer){
 ARG_UNUSED(timer);uint32_t now=k_uptime_get_32();uint8_t selected,b=(uint8_t)atomic_get(&battery);
 view.keyboard=(struct panel_status){.side=IS_ENABLED(CONFIG_SHIELD_VELVET_LEFT)?'L':'R',
 .connected=zmk_split_bt_peripheral_is_connected(),.battery_valid=b<=100,.battery=b};
 k_spinlock_key_t key=k_spin_lock(&lock);selected=theme;bool known=theme_known;
 view.keyboard.layer=layer.layer;view.keyboard.layer_valid=view.keyboard.connected&&cat_layer_live(&layer,now);
 bool fresh=received&&view.keyboard.connected&&(uint32_t)(now-received_at)<3000u;
 view.keyboard.output=fresh?output:DASH_OUTPUT_NONE;
 view.keyboard.profile=fresh?profile:0;
 memcpy(view.data,host,sizeof(host));k_spin_unlock(&lock,key);
 if(!fresh)view.data[1]=0;
 if(!(view.data[1]&DASH_CPU)){view.count=0;history_started=false;}
 else if(!history_started||history_sequence!=view.data[2]){
  history_started=true;history_sequence=view.data[2];
  if(view.count<12)view.history[view.count++]=view.data[3];
  else {memmove(view.history,view.history+1,11);view.history[11]=view.data[3];}
 }

 if(!known)memset(packed,0xff,sizeof(packed));
 else if(selected==0){struct cat_status c={.connected=view.keyboard.connected,
 .battery_valid=view.keyboard.battery_valid,.battery=b,.layer_valid=view.keyboard.layer_valid,.layer=view.keyboard.layer};cat_render(packed,c);}
 else if(IS_ENABLED(CONFIG_SHIELD_VELVET_LEFT))codex_render(packed,&view);else system_render(packed,&view);
 cat_expand_l8(packed,gray);lv_obj_invalidate(image);atomic_inc(&drawn_count);
}
lv_obj_t *zmk_display_status_screen(void){
 lv_obj_t *screen=lv_obj_create(NULL);lv_obj_set_style_bg_color(screen,lv_color_white(),0);
 lv_obj_set_style_bg_opa(screen,LV_OPA_COVER,0);lv_obj_set_style_pad_all(screen,0,0);
 lv_obj_set_style_border_width(screen,0,0);lv_obj_remove_flag(screen,LV_OBJ_FLAG_SCROLLABLE);
 image=lv_image_create(screen);lv_image_set_src(image,&source);lv_obj_set_pos(image,0,0);
 refresh(NULL);lv_timer_create(refresh,1000,NULL);return screen;
}

/* An independent heartbeat distinguishes stopped LVGL refresh from lost RX. */
static void publish_display_ack(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(display_ack_work,publish_display_ack);
static void publish_display_ack(struct k_work *work) {
 ARG_UNUSED(work);
 struct zmk_split_transport_peripheral_event event={
  .type=ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_RELAY_EVENT,
  .data.relay_event.header={.event_type_size=sizeof(DASH_ACK_EVENT)-1,.event_data_size=DASH_ACK_SIZE}};
 strcpy(event.data.relay_event.event_type,DASH_ACK_EVENT);
 bool connected=zmk_split_bt_peripheral_is_connected();
 k_spinlock_key_t key=k_spin_lock(&lock);
 uint8_t selected=theme;
 bool fresh=received&&connected&&(uint32_t)(k_uptime_get_32()-received_at)<3000u;
 k_spin_unlock(&lock,key);
 dash_ack_encode(event.data.relay_event.event_data,IS_ENABLED(CONFIG_SHIELD_VELVET_LEFT)?0:1,
                 selected,connected,fresh,(uint32_t)atomic_get(&received_count),
                 (uint32_t)atomic_get(&drawn_count));
 (void)zmk_split_peripheral_report_event(&event);
 k_work_reschedule(&display_ack_work,K_SECONDS(2));
}
static int init_display_ack(void) {
 k_work_schedule(&display_ack_work,K_SECONDS(3));return 0;
}
SYS_INIT(init_display_ack,APPLICATION,90);
