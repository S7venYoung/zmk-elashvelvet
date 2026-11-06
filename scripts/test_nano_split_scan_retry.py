#!/usr/bin/env python3
"""Compile and exercise the patched scan state machine with host mocks."""
from pathlib import Path
import subprocess
import sys
import tempfile


def function(text, name):
    prefix = f"static int {name}(void) {{"
    callback_prefix = f"static void {name}(struct k_work *work) {{"
    start = text.find(prefix)
    if start < 0:
        start = text.find(callback_prefix)
    if start < 0:
        raise AssertionError(f"Missing patched function {name}")
    brace = text.index("{", start)
    depth = 0
    for pos in range(brace, len(text)):
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
            if depth == 0:
                return text[start:pos + 1]
    raise AssertionError(f"Unterminated function {name}")


upstream = Path(sys.argv[1])
patcher = Path(__file__).with_name("patch_nano_split_scan_retry.py")

with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    source = temp / "central.c"
    source.write_text(upstream.read_text())
    subprocess.run([sys.executable, str(patcher), str(source)], check=True)
    first = source.read_text()
    assert "VELVET_NANO_SPLIT_SCAN_RECOVERY" in first
    subprocess.run([sys.executable, str(patcher), str(source)], check=True)
    assert source.read_text() == first

harness = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS 3
#define BT_LE_SCAN_PASSIVE 0
#define K_SECONDS(value) ((value) * 1000)
#define ARG_UNUSED(value) ((void)(value))
#define LOG_DBG(...) ((void)0)
#define LOG_ERR(...) ((void)0)
#define LOG_WRN(...) ((void)0)

struct k_work { int unused; };
struct k_work_delayable { int unused; };
struct bt_conn { int unused; };
enum peripheral_slot_state {
    PERIPHERAL_SLOT_STATE_OPEN,
    PERIPHERAL_SLOT_STATE_CONNECTING,
    PERIPHERAL_SLOT_STATE_CONNECTED,
};
struct peripheral_slot {
    enum peripheral_slot_state state;
    struct bt_conn *conn;
};

static bool is_enabled = true;
static bool is_scanning;
static struct peripheral_slot peripherals[CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS];
static struct k_work_delayable split_central_scan_retry_work;
static int scan_starts;
static int scan_stops;
static int scan_start_error;
static int reschedules;
static int cancels;
static int retry_delay;
#define SPLIT_CENTRAL_SCAN_RETRY_DELAY K_SECONDS(1)
#define SPLIT_CENTRAL_SCAN_HEALTH_DELAY K_SECONDS(10)

static void split_central_device_found(int unused) { ARG_UNUSED(unused); }
static int start_scanning(void);

static int bt_le_scan_start(int options, void (*callback)(int)) {
    ARG_UNUSED(options);
    ARG_UNUSED(callback);
    scan_starts++;
    return scan_start_error;
}

static int bt_le_scan_stop(void) {
    scan_stops++;
    return 0;
}

static int k_work_reschedule(struct k_work_delayable *work, int delay) {
    ARG_UNUSED(work);
    reschedules++;
    retry_delay = delay;
    return 0;
}

static int k_work_cancel_delayable(struct k_work_delayable *work) {
    ARG_UNUSED(work);
    cancels++;
    retry_delay = 0;
    return 0;
}
'''

functions = "\n\n".join(
    function(first, name)
    for name in (
        "stop_scanning",
        "split_central_scan_retry_cb",
        "start_scanning",
    )
)

tests = r'''
int main(void) {
    /* A failed hardware start cannot leave the stale permanent flag. */
    scan_start_error = -EIO;
    assert(start_scanning() == -EIO);
    assert(!is_scanning);
    assert(scan_starts == 1);
    assert(reschedules == 1 && retry_delay == 1000);

    /* The work callback invokes the real patched state machine again. */
    split_central_scan_retry_cb(NULL);
    assert(scan_starts == 2);
    assert(!is_scanning && reschedules == 2);

    /* Successful recovery arms only the ten-second health guard. */
    scan_start_error = 0;
    reschedules = 0;
    split_central_scan_retry_cb(NULL);
    assert(scan_starts == 3 && is_scanning);
    assert(reschedules == 1 && retry_delay == 10000);
    int starts = scan_starts;
    assert(start_scanning() == 0);
    assert(scan_starts == starts);

    /* The health work refreshes controller scanning instead of trusting the
     * host-side -EALREADY state. */
    cancels = 0;
    reschedules = 0;
    split_central_scan_retry_cb(NULL);
    assert(scan_stops == 1);
    assert(scan_starts == starts + 1 && is_scanning);
    assert(reschedules == 1 && retry_delay == 10000);

    /* Do not collide with an in-flight connection attempt. */
    peripherals[1].state = PERIPHERAL_SLOT_STATE_CONNECTING;
    starts = scan_starts;
    reschedules = 0;
    split_central_scan_retry_cb(NULL);
    assert(scan_starts == starts && is_scanning);
    assert(reschedules == 1 && retry_delay == 10000);
    peripherals[1].state = PERIPHERAL_SLOT_STATE_OPEN;

    /* Stop clears both software state and any pending retry. */
    assert(stop_scanning() == 0);
    assert(!is_scanning && scan_stops == 2);

    /* A host that already owns a scan is success, not a retry storm. */
    scan_start_error = -EALREADY;
    reschedules = 0;
    assert(start_scanning() == 0);
    assert(is_scanning && reschedules == 1 && retry_delay == 10000);
    assert(start_scanning() == 0);
    assert(reschedules == 2 && retry_delay == 10000);
    assert(stop_scanning() == 0);

    /* Disabled transport and a fully connected topology do not scan or retry. */
    is_enabled = false;
    starts = scan_starts;
    reschedules = 0;
    assert(start_scanning() == 0);
    assert(scan_starts == starts && reschedules == 0);

    is_enabled = true;
    struct bt_conn connections[CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS];
    for (int i = 0; i < CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS; i++) {
        peripherals[i].conn = &connections[i];
        peripherals[i].state = PERIPHERAL_SLOT_STATE_CONNECTED;
    }
    starts = scan_starts;
    assert(start_scanning() == 0);
    assert(scan_starts == starts && reschedules == 0);
    return 0;
}
'''

with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    c_path = temp / "test.c"
    c_path.write_text(harness + functions + tests)
    executable = temp / "test"
    subprocess.run(
        ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(c_path), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)

print("Nano split scan recovery: failure, retry, health restart, connecting, EALREADY, stop and idle cases passed")
