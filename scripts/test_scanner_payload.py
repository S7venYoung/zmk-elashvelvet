#!/usr/bin/env python3
"""Compile the actual packet selector; check timing, protocol and wraparound."""
from pathlib import Path
import subprocess
import tempfile
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    (out / "zephyr/sys").mkdir(parents=True)
    (out / "zmk").mkdir()
    (out / "zephyr/sys/util.h").write_text("")
    (out / "zmk/hid.h").write_text("""
#include <stdint.h>
struct zmk_hid_keyboard_report { struct { uint8_t modifiers; } body; };
struct zmk_hid_keyboard_report *zmk_hid_get_keyboard_report(void);
""")
    (out / "test.c").write_text(r"""
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <zmk/hid.h>
#include "scanner_payload.h"
static struct zmk_hid_keyboard_report report = {{8}};
struct zmk_hid_keyboard_report *zmk_hid_get_keyboard_report(void) { return &report; }
void fight_telemetry_read(uint8_t wpm[2], uint8_t battery[2], uint8_t *valid) {
    wpm[0]=17; wpm[1]=24; battery[0]=0; battery[1]=75; *valid=7;
}
int main(void) {
    uint8_t status[26] = {255,255,0xab,0xcd}, id[4] = {1,2,3,4};
    unsigned count=0, last=0, max_gap=0;
    for (unsigned tick=1; tick<=140000; ++tick) {
        size_t size;
        const uint8_t *p=velvet_scanner_payload(status,sizeof(status),id,&size);
        if (tick%2) {
            assert(size==26 && p==status && p[3]==0xcd);
            continue;
        }
        assert(size==17 && p[0]==255 && p[1]==255 && p[2]==0xab && p[3]==0xce);
        assert(p[4]==1 && p[5]==7 && !memcmp(p+6,id,4));
        assert(p[10]==17 && p[11]==24 && p[12]==0 && p[13]==75 && p[14]==8);
        assert(((unsigned)p[15] | (unsigned)p[16]<<8)==(uint16_t)count);
        ++count;
        unsigned gap=(tick-last)*200; // worst configured idle interval
        if(gap>max_gap)max_gap=gap;
        last=tick;
    }
    assert(count==70000 && max_gap==400 && max_gap<3000);
    return 0;
}
""")
    subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-I"+str(out), "-I"+str(root/"src"),
                    str(root/"src/scanner_payload.c"), str(out/"test.c"),
                    "-o", str(out/"test")], check=True)
    subprocess.run([str(out/"test")], check=True)
conf=(root/"boards/shields/velvet/velvet_nano_dongle.conf").read_text()
assert "CONFIG_ZMK_STATUS_ADV_ACTIVE_INTERVAL_MS=100\n" in conf
assert "CONFIG_ZMK_STATUS_ADV_IDLE_INTERVAL_MS=200\n" in conf
assert "CONFIG_BT_EXT_ADV=n\n" in conf
print("Cube cadence: 400ms worst idle gap; packet values and sequence wrap passed")
