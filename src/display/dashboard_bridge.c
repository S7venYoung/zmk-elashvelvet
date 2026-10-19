/* SPDX-License-Identifier: MIT */
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/init.h>
#include <zephyr/sys/atomic.h>
#include <zmk/event_manager.h>
#include <zmk/split/central.h>
#include <cormoran/zmk/custom_settings.h>
#include <zmk/studio/custom.h>
#include "common/dashboard_data.h"

static struct zmk_rpc_custom_subsystem_meta meta={ZMK_RPC_CUSTOM_SUBSYSTEM_UI_URLS(),
 .security=ZMK_STUDIO_RPC_HANDLER_UNSECURED};
static bool no_direct_request(const zmk_custom_CallRequest *req,pb_callback_t *res){
 ARG_UNUSED(req);ARG_UNUSED(res);return false;
}
ZMK_RPC_CUSTOM_SUBSYSTEM(velvet_display,&meta,no_direct_request);
#define THEME_SETTING(name,key,value) \
 ZMK_CUSTOM_SETTING_DEFINE(name,"velvet_display",key,ZMK_CUSTOM_SETTING_VALUE_TYPE_INT32, \
 ZMK_CUSTOM_SETTING_VALUE_INT32(value),ZMK_CUSTOM_SETTING_CONFIDENTIALITY_RPC_PUBLIC, \
 ZMK_CUSTOM_SETTING_PERMISSION_UNSECURE,ZMK_CUSTOM_SETTING_PERMISSION_UNSECURE, \
 ZMK_CUSTOM_SETTING_RANGE_INT32(0,1))
THEME_SETTING(theme_set,"theme_set",0);
ZMK_CUSTOM_SETTING_DEFINE(host_metrics,"velvet_display","host_metrics",ZMK_CUSTOM_SETTING_VALUE_TYPE_BYTES,
 ZMK_CUSTOM_SETTING_VALUE_BYTES(1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
 ZMK_CUSTOM_SETTING_CONFIDENTIALITY_RPC_PERSONAL,ZMK_CUSTOM_SETTING_PERMISSION_UNSECURE,
 ZMK_CUSTOM_SETTING_PERMISSION_UNSECURE,ZMK_CUSTOM_SETTING_NO_CONSTRAINT);
static atomic_t dirty;
static uint8_t last[DASH_DATA_SIZE]={1};
static uint32_t updated;
static bool live;
static int on_settings(const zmk_event_t *eh){
 const struct zmk_custom_setting_changed *e=as_zmk_custom_setting_changed(eh);
 if(e&&e->kind==ZMK_CUSTOM_SETTING_CHANGED_VALUE_UPDATED&&
 !strcmp(e->setting->custom_subsystem_id,"velvet_display")&&!strcmp(e->setting->key,"host_metrics"))atomic_set(&dirty,1);
 return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(velvet_dashboard_settings,on_settings);
ZMK_SUBSCRIPTION(velvet_dashboard_settings,zmk_custom_setting_changed);
static void send_snapshot(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(publish_work,send_snapshot);
static void send_snapshot(struct k_work *work){
 ARG_UNUSED(work);uint32_t now=k_uptime_get_32();
 if(atomic_set(&dirty,0)){
  uint8_t data[DASH_DATA_SIZE];size_t len=0;
  int rc=zmk_custom_setting_read_into(zmk_custom_setting_find("velvet_display","host_metrics"),data,sizeof(data),&len,NULL);
  if(!rc&&dash_valid(data,len)){memcpy(last,data,sizeof(last));updated=now;live=true;}
 }
 struct zmk_split_relay_event_payload payload={.header.event_type_size=sizeof(DASH_EVENT)-1,
 .header.event_data_size=DASH_PACKET_SIZE};
 strcpy(payload.event_type,DASH_EVENT);uint8_t*p=payload.event_data;p[0]=1;
 int32_t selected=0;
 zmk_custom_setting_get_int32(zmk_custom_setting_find("velvet_display","theme_set"),&selected);
 p[1]=p[2]=selected==1?1:0;

 dash_age_data(p+3,last,live,now-updated);
 zmk_split_central_send_relay_event(&payload);
 k_work_reschedule(&publish_work,K_SECONDS(1));
}
static int start(void){k_work_schedule(&publish_work,K_SECONDS(3));return 0;}
SYS_INIT(start,APPLICATION,CONFIG_APPLICATION_INIT_PRIORITY);
