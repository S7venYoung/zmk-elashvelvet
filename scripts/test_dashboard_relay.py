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
#define DASH_PACKET_SIZE 21
''' + structs + '\n' + header.replace('#include <zmk/split/transport/types.h>', '').replace('#pragma once', '') + r'''
static void roundtrip(struct zmk_split_relay_event_payload *p, const char *name, unsigned size) {
    assert(p->header.event_type_size == strlen(name));
    assert(p->header.event_data_size == size);
    for (unsigned i=0;i<size;i++) p->event_data[i]=(uint8_t)(i+1);
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
}
int main(void) {
''' + '\n'.join(cases) + '\nputs("Dashboard and layer relay names and bytes survive BLE chunking");\n}\n'
with tempfile.TemporaryDirectory() as d:
    source = pathlib.Path(d) / 'test.c'
    binary = pathlib.Path(d) / 'test'
    source.write_text(program)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
