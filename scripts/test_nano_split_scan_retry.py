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
#define BT_HCI_ERR_REMOTE_USER_TERM_CONN 19
typedef struct { int milliseconds; } k_timeout_t;
#define K_SECONDS(value) ((k_timeout_t){(value) * 1000})
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
    int64_t connecting_since;
    bool connection_abort_requested;
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
static int64_t uptime_ms = 100000;
static int disconnect_calls;
static int release_calls;
static int disconnect_error;

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

static int64_t k_uptime_get(void) { return uptime_ms; }

static int bt_conn_disconnect(struct bt_conn *conn, uint8_t reason) {
    ARG_UNUSED(conn);
    ARG_UNUSED(reason);
    disconnect_calls++;
    return disconnect_error;
}

static int release_peripheral_slot(int index) {
    release_calls++;
    peripherals[index].conn = NULL;
    peripherals[index].state = PERIPHERAL_SLOT_STATE_OPEN;
    peripherals[index].connecting_since = 0;
    peripherals[index].connection_abort_requested = false;
    return 0;
}

static int k_work_reschedule(struct k_work_delayable *work, k_timeout_t delay) {
    ARG_UNUSED(work);
    reschedules++;
    retry_delay = delay.milliseconds;
    return 0;
}

static int k_work_cancel_delayable(struct k_work_delayable *work) {
    ARG_UNUSED(work);
    cancels++;
    retry_delay = 0;
    return 0;
}
'''

defines = "\n".join(line for line in first.splitlines()
                    if line.startswith("#define SPLIT_CENTRAL_"))
functions = defines + "\n\n" + "\n\n".join(
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
    assert(reschedules == 1 && retry_delay == 2000);
    peripherals[1].state = PERIPHERAL_SLOT_STATE_OPEN;

    /* A stale CONNECTING slot is aborted, then force-released if the abort
     * callback never arrives. */
    struct bt_conn stuck_conn;
    peripherals[1].conn = &stuck_conn;
    peripherals[1].state = PERIPHERAL_SLOT_STATE_CONNECTING;
    peripherals[1].connecting_since = uptime_ms - 16000;
    peripherals[1].connection_abort_requested = false;
    starts = scan_starts;
    reschedules = 0;
    split_central_scan_retry_cb(NULL);
    assert(disconnect_calls == 1 && release_calls == 0);
    assert(peripherals[1].state == PERIPHERAL_SLOT_STATE_CONNECTING);
    assert(scan_starts == starts && reschedules == 1 && retry_delay == 2000);

    uptime_ms += 2000;
    reschedules = 0;
    split_central_scan_retry_cb(NULL);
    assert(release_calls == 1);
    assert(peripherals[1].state == PERIPHERAL_SLOT_STATE_OPEN);
    assert(peripherals[1].conn == NULL);
    assert(scan_starts == starts + 1 && is_scanning);
    assert(reschedules == 1 && retry_delay == 10000);

    /* Stop clears both software state and any pending retry. */
    assert(stop_scanning() == 0);
    assert(!is_scanning && scan_stops == 3);

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

print("Nano split scan recovery: failure, retry, health restart, stale connecting, EALREADY, stop and idle cases passed")
