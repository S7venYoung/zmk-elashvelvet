#!/usr/bin/env python3
"""Host regression: send production display payloads through ZMK BLE chunking."""
import pathlib
import re
import subprocess
import sys
import tempfile

root = pathlib.Path(__file__).resolve().parents[1]
zmk = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'dependencies/zmk'
types = (zmk / 'app/include/zmk/split/transport/types.h').read_text()
header = (zmk / 'app/src/split/bluetooth/relay_event.h').read_text()
structs = '\n'.join(re.search(r'struct ' + name + r' \{.*?\} __packed;', types, re.S)[0]
                    for name in ['relay_event_header', 'zmk_split_relay_event_payload'])

receiver=(root / "src/display/dashboard_screen.c").read_text()
receiver=receiver[receiver.index("static int on_event("):receiver.index("ZMK_LISTENER(velvet_dashboard,")]
cases = []
for file, event, size in [('src/display/dashboard_bridge.c', 'DASH_EVENT', 21),
                          ('src/display/themes/cat/cat_layer_relay.c', 'CAT_LAYER_EVENT', 2)]:
    text = (root / file).read_text()
    init = re.search(r'struct zmk_split_relay_event_payload payload\s*=\s*\{.*?\};', text, re.S)[0]
    copy = re.search(r'strcpy\(payload.event_type,\s*' + event + r'\);', text)[0]
    cases.append('{' + init + copy + f' roundtrip(&payload, {event}, {size});' + '}')

program = r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#define __packed __attribute__((packed))
#define CONFIG_ZMK_SPLIT_RELAY_EVENT 1
#define CONFIG_ZMK_SPLIT_RELAY_EVENT_TYPE_NAME_LEN 32
#define CONFIG_ZMK_SPLIT_RELAY_EVENT_DATA_LEN 64
#define IS_ENABLED(x) (x)
#define BIT(x) (1u << (x))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define DASH_EVENT "vldash"
#define CAT_LAYER_EVENT "vlcat"
#include "dashboard_data.h"
#include "dashboard_debug.h"
#include "cat_layer.h"
#define ZMK_EV_EVENT_BUBBLE 0
#define ZMK_EV_EVENT_HANDLED 1
typedef int atomic_t;
static void atomic_set(atomic_t *p,int n){*p=n;}
static void atomic_inc(atomic_t *p){++*p;}
struct k_spinlock {int unused;};
typedef int k_spinlock_key_t;
static int k_spin_lock(struct k_spinlock *p){(void)p;return 0;}
static void k_spin_unlock(struct k_spinlock *p,int key){(void)p;(void)key;}
static uint32_t k_uptime_get_32(void){return 1000;}
struct zmk_battery_state_changed {uint8_t state_of_charge;};
struct zmk_relay_event_received {const char *event_name;const uint8_t *event_data;unsigned event_data_size;};
typedef struct {int kind;const void *data;} zmk_event_t;
static const struct zmk_battery_state_changed *as_zmk_battery_state_changed(const zmk_event_t *e){return e->kind==1?e->data:NULL;}
static const struct zmk_relay_event_received *as_zmk_relay_event_received(const zmk_event_t *e){return e->kind==2?e->data:NULL;}
static atomic_t battery,received_count;
static struct k_spinlock lock;
static struct cat_layer_sample layer;
static uint8_t host[DASH_DATA_SIZE],theme;
static uint32_t received_at;
static bool received;
''' + receiver + '\n' + structs + '\n' + header.replace('#include <zmk/split/transport/types.h>', '').replace('#pragma once', '') + r'''
static void roundtrip(struct zmk_split_relay_event_payload *p, const char *name, unsigned size) {
    assert(p->header.event_type_size == strlen(name));
    assert(p->header.event_data_size == size);
    memset(p->event_data,0,size);
    p->event_data[0]=1;
    if(size==DASH_PACKET_SIZE){p->event_data[1]=p->event_data[2]=1;p->event_data[3]=1;}
    else p->event_data[1]=2;
    uint16_t total;
    assert(zmk_split_relay_event_payload_total_size(p,&total)==0);
    struct zmk_split_relay_event_chunk_reassembly_state state={0};
    unsigned seq=0;
    for (unsigned offset=0;offset<total;) {
        uint8_t bytes[7];
        unsigned n=MIN(sizeof(bytes),total-offset);
        zmk_split_relay_event_copy_payload_data(p,offset,bytes,n);
        bool end=offset+n==total;
        struct relay_event_header h={.sequence=seq++|(end?128:0),
            .event_type_size=p->header.event_type_size,.event_data_size=n};
        assert(zmk_split_relay_event_chunk_reassembly_accept(&state,&h,bytes,n)==(end?1:0));
        offset+=n;
    }
    assert(strcmp(state.payload.event_type,name)==0);
    assert(state.payload.header.event_data_size==size);
    assert(memcmp(state.payload.event_data,p->event_data,size)==0);
    struct zmk_relay_event_received event={.event_name=state.payload.event_type,
      .event_data=state.payload.event_data,.event_data_size=state.payload.header.event_data_size};
    zmk_event_t wrapped={.kind=2,.data=&event};
    assert(on_event(&wrapped)==ZMK_EV_EVENT_HANDLED);
    if(size==DASH_PACKET_SIZE){assert(theme==1&&received&&received_count==1&&received_at==1000);}
    else {assert(layer.seen&&layer.layer==2);}
    /* An unrelated relay must not consume or change display state. */
    event.event_name="unrelated";
    assert(on_event(&wrapped)==ZMK_EV_EVENT_BUBBLE);
}
int main(void) {
''' + '\n'.join(cases) + '\nputs("Dashboard and layer relay names and bytes survive BLE chunking");\n}\n'
with tempfile.TemporaryDirectory() as d:
    source = pathlib.Path(d) / 'test.c'
    binary = pathlib.Path(d) / 'test'
    source.write_text(program)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I'+str(root/'src/display/common'), '-I'+str(root/'src/display/themes/cat'), str(source), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
