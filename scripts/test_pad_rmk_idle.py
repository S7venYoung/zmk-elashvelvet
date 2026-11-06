#!/usr/bin/env python3
"""Exercise the actual patched advertising callbacks with host Bluetooth/work mocks."""
from pathlib import Path
import subprocess
import sys
import tempfile

upstream = Path(sys.argv[1]).read_text()
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    patched = tmp / 'peripheral.c'
    patched.write_text(upstream)
    patcher = Path(__file__).with_name('patch_pad_rmk_idle.py')
    subprocess.run([sys.executable, str(patcher), str(patched)], check=True)
    first = patched.read_text()
    subprocess.run([sys.executable, str(patcher), str(patched)], check=True)
    assert patched.read_text() == first
    section = first[first.index('/* EYELASH_RMK_ADVERTISING_SLEEP */'):first.index('static void recycled(void)')]
    section = '\n'.join(line for line in section.splitlines() if not line.startswith('#include'))
    # The opening #if precedes the marker in the real source.
    section = '#if 1\n' + section
    harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <errno.h>
#include <stdint.h>
#define IS_ENABLED(x) 1
#define CONFIG_SHIELD_EYELASH_NUMPAD 1
#define K_SECONDS(x) (x)
#define LOG_ERR(...) ((void)0)
#define ZMK_EV_EVENT_BUBBLE 0
#define BT_HCI_ERR_ADV_TIMEOUT 60
#define ZMK_LISTENER(...)
#define ZMK_SUBSCRIPTION(...)
typedef int atomic_t;
static int atomic_get(atomic_t *p) { return *p; }
static void atomic_set(atomic_t *p,int n) { *p=n; }
static void atomic_clear(atomic_t *p) { *p=0; }
struct k_work { void (*fn)(struct k_work *); };
struct delayable { struct k_work work; int delay; };
#define K_WORK_DEFINE(n,cb) struct k_work n={cb}
#define K_WORK_DELAYABLE_DEFINE(n,cb) struct delayable n={{cb},0}
static void k_work_submit(struct k_work *w) { w->fn(w); }
static void k_work_schedule(struct delayable *w,int delay) { if(!w->delay)w->delay=delay; }
static void k_work_cancel_delayable(struct delayable *w) { w->delay=0; }
struct zmk_position_state_changed { bool state; };
typedef struct zmk_position_state_changed zmk_event_t;
static const struct zmk_position_state_changed *as_zmk_position_state_changed(const zmk_event_t *e) { return e; }
struct zmk_split_peripheral_status_changed { bool connected; };
static void raise_zmk_split_peripheral_status_changed(struct zmk_split_peripheral_status_changed s) {}
struct bt_conn {};
static bool enabled=true,is_connected=false,low_duty_advertising=false;
static int starts,stops,start_error,stop_error;
static int start_advertising(bool low) { starts++;return start_error; }
static int bt_le_adv_stop(void) { stops++;return stop_error; }
'''
    tests = r'''
int main(void) {
    advertising_cb(0); assert(starts==1 && pad_advertising_timeout.delay==300);
    pad_advertising_timeout.delay=100;
    low_duty_advertising=true; advertising_cb(0);
    assert(pad_advertising_timeout.delay==100); // fallback doesn't restart budget
    connected(0,0); assert(is_connected && !pad_advertising_timeout.delay);
    pad_advertising_timeout_cb(0); assert(!stops && !pad_advertising_asleep);
    advertising_cb(0); assert(starts==2); // connected link left alone
    zmk_event_t release={false},press={true};
    is_connected=false; atomic_clear(&pad_advertising_active);
    pad_key_wake_listener(&press); assert(starts==3 && !pad_advertising_asleep);
    assert(pad_advertising_timeout.delay==300);
    pad_key_wake_listener(&press); assert(starts==3); // active advertiser is not restarted
    pad_advertising_timeout.delay=0; pad_advertising_timeout_cb(0);
    assert(stops==1 && pad_advertising_asleep);
    recycled_unused: ;
    advertising_cb(0); assert(starts==3); // pending advertising can't defeat sleep
    pad_key_wake_listener(&release); assert(starts==3);
    pad_key_wake_listener(&press); assert(starts==4 && !pad_advertising_asleep);
    assert(!low_duty_advertising && pad_advertising_timeout.delay==300);
    pad_key_wake_listener(&press); assert(starts==4); // no restart on every key
    stop_error=-EIO; pad_advertising_timeout_cb(0); assert(!pad_advertising_asleep);
    stop_error=-EALREADY; pad_advertising_timeout_cb(0); assert(pad_advertising_asleep);
    enabled=false; pad_key_wake_listener(&press); advertising_cb(0); assert(starts==4);
    enabled=true; connected(0,0); assert(!pad_advertising_asleep);
    is_connected=false; start_error=-EIO; advertising_cb(0);
    assert(!pad_advertising_timeout.delay); // failed starts don't arm timer
    return 0;
}
'''
    c = tmp / 'test.c'
    c.write_text(harness + section + tests.replace('    recycled_unused: ;\n',''))
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Wno-unused-parameter',str(c),'-o',str(tmp/'test')], check=True)
    subprocess.run([str(tmp/'test')], check=True)
print('Patched Pad callbacks: timeout, connected guard, key wake, retry and idempotence passed')
