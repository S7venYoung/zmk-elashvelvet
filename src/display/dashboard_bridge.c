/* SPDX-License-Identifier: MIT */
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/init.h>
#include <zephyr/sys/atomic.h>
#include <zmk/event_manager.h>
#include <zmk/split/central.h>
#include <zmk/endpoints.h>
#include <cormoran/zmk/custom_settings.h>
#include <zmk/studio/custom.h>
#include "common/dashboard_data.h"
#include "common/dashboard_debug.h"
#include <pb_encode.h>

BUILD_ASSERT(sizeof(DASH_EVENT)-1 <= CONFIG_ZMK_SPLIT_RELAY_EVENT_TYPE_NAME_LEN,
             "DASH_EVENT exceeds split relay event-name capacity");
BUILD_ASSERT(sizeof(DASH_ACK_EVENT)-1 <= CONFIG_ZMK_SPLIT_RELAY_EVENT_TYPE_NAME_LEN,
             "DASH_ACK_EVENT exceeds split relay event-name capacity");

BUILD_ASSERT(ZMK_BLE_PROFILE_COUNT==DASH_BLE_PROFILES,
             "Display expects five host BLE profiles");

static struct zmk_rpc_custom_subsystem_meta meta={ZMK_RPC_CUSTOM_SUBSYSTEM_UI_URLS(),
 .security=ZMK_STUDIO_RPC_HANDLER_UNSECURED};
/* RAM-only observations; never create another persistable Custom Setting. */
static struct k_spinlock debug_lock;
static uint8_t debug_response[DASH_DEBUG_SIZE];
static uint8_t acknowledgements[2][DASH_ACK_SIZE];
static uint32_t acknowledgement_at[2];
static bool acknowledgement_seen[2];
static uint32_t tx_count, ack_count;
static uint8_t selected_theme;
static int setting_result, queue_result;
static bool encode_debug(pb_ostream_t *stream,const pb_field_t *field,void *const *arg) {
 ARG_UNUSED(arg);
 /* CallResponse.payload contains protobuf field 1: bytes status. */
 return pb_encode_tag_for_field(stream,field)&&pb_encode_varint(stream,DASH_DEBUG_SIZE+2)&&
        pb_encode_tag(stream,PB_WT_STRING,1)&&pb_encode_string(stream,debug_response,sizeof(debug_response));
}
static bool read_debug(const zmk_custom_CallRequest *req,pb_callback_t *res) {
 if(req->payload.size!=2||req->payload.bytes[0]!=8||req->payload.bytes[1]!=1)return false;
 uint32_t now=k_uptime_get_32();
 k_spinlock_key_t key=k_spin_lock(&debug_lock);
 memset(debug_response,0,sizeof(debug_response));
 debug_response[0]=1;debug_response[1]=selected_theme;
 debug_response[2]=(uint8_t)setting_result;debug_response[3]=(uint8_t)queue_result;
 dash_debug_put32(debug_response+4,tx_count);dash_debug_put32(debug_response+8,ack_count);
 memcpy(debug_response+12,acknowledgements[0],DASH_ACK_SIZE);
 memcpy(debug_response+24,acknowledgements[1],DASH_ACK_SIZE);
 dash_debug_put32(debug_response+36,acknowledgement_seen[0]?now-acknowledgement_at[0]:UINT32_MAX);
 dash_debug_put32(debug_response+40,acknowledgement_seen[1]?now-acknowledgement_at[1]:UINT32_MAX);
 dash_debug_put32(debug_response+44,now);
 k_spin_unlock(&debug_lock,key);
 res->funcs.encode=encode_debug;res->arg=NULL;return true;
}
ZMK_RPC_CUSTOM_SUBSYSTEM(velvet_display,&meta,read_debug);
static int receive_ack(const zmk_event_t *eh) {
 const struct zmk_relay_event_received *e=as_zmk_relay_event_received(eh);
 if(!e||!e->event_name||strcmp(e->event_name,DASH_ACK_EVENT)||
    !dash_ack_valid(e->event_data,e->event_data_size))return ZMK_EV_EVENT_BUBBLE;
 unsigned side=e->event_data[1];
 k_spinlock_key_t key=k_spin_lock(&debug_lock);
 memcpy(acknowledgements[side],e->event_data,DASH_ACK_SIZE);
 acknowledgement_at[side]=k_uptime_get_32();acknowledgement_seen[side]=true;ack_count++;
 k_spin_unlock(&debug_lock,key);return ZMK_EV_EVENT_HANDLED;
}
ZMK_LISTENER(velvet_dashboard_ack,receive_ack);
ZMK_SUBSCRIPTION(velvet_dashboard_ack,zmk_relay_event_received);
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
 strcpy(payload.event_type,DASH_EVENT);uint8_t*p=payload.event_data;p[0]=DASH_PACKET_VERSION;
 int32_t selected=0;
 int get_result=zmk_custom_setting_get_int32(zmk_custom_setting_find("velvet_display","theme_set"),&selected);
 p[1]=selected==1?1:0;
 struct zmk_endpoint_instance endpoint=zmk_endpoint_get_selected();
 p[2]=DASH_OUTPUT_NONE;p[3]=0;
 if(endpoint.transport==ZMK_TRANSPORT_USB)p[2]=DASH_OUTPUT_USB;
 else if(endpoint.transport==ZMK_TRANSPORT_BLE&&endpoint.ble.profile_index>=0&&
         endpoint.ble.profile_index<DASH_BLE_PROFILES){
  p[2]=DASH_OUTPUT_BLE;p[3]=(uint8_t)(endpoint.ble.profile_index+1);
 }

 dash_age_data(p+DASH_PACKET_HEADER_SIZE,last,live,now-updated);
 int send_result=zmk_split_central_send_relay_event(&payload);
 k_spinlock_key_t key=k_spin_lock(&debug_lock);
 selected_theme=p[1];setting_result=get_result;queue_result=send_result;tx_count++;
 k_spin_unlock(&debug_lock,key);
 k_work_reschedule(&publish_work,K_SECONDS(1));
}
static int start(void){k_work_schedule(&publish_work,K_SECONDS(3));return 0;}
SYS_INIT(start,APPLICATION,CONFIG_APPLICATION_INIT_PRIORITY);
