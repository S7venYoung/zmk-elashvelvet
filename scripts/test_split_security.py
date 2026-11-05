"""Host-test the patched Nano split security and CCC retry state machine."""

from pathlib import Path
import subprocess
import sys
import tempfile

from patch_split_security import patch


def function(source, name):
    search = 0
    while True:
        start = source.index(name, search)
        opening = source.find("{", start)
        semicolon = source.find(";", start)
        if semicolon < 0 or opening < semicolon:
            break
        search = start + 1
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


source = Path(sys.argv[1]).read_text()
patched = patch(source)
assert patch(patched) == patched
for marker in (
    "VELVET_SPLIT_SECURITY_GATE",
    "VELVET_SPLIT_SUBSCRIPTION_RETRY",
    "split_central_cancel_subscribe_retry(slot);",
    "params->subscribe = split_central_subscribe_complete;",
    "split_central_resume_subscribe_retries(slot);",
):
    assert marker in patched, marker

prefix = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define BIT(n) (1u << (n))
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define CONTAINER_OF(ptr, type, member) ((type *)((char *)(ptr) - offsetof(type, member)))
#define IS_ENABLED(value) (value)
#define ZMK_KEYMAP_HAS_SENSORS 1
#define CONFIG_ZMK_SPLIT_RELAY_EVENT 1
#define CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING 1
#define ZMK_SPLIT_BLE_PERIPHERAL_COUNT 1
#define K_MSEC(value) (value)
#define K_NO_WAIT 0
#define LOG_DBG(...) ((void)0)
#define LOG_WRN(...) ((void)0)
#define LOG_ERR(...) ((void)0)
#define BT_SECURITY_L2 2
#define BT_GATT_SUBSCRIBE_FLAG_NO_RESUB 0
#define BT_ATT_FIRST_ATTRIBUTE_HANDLE 1
#define BT_ATT_LAST_ATTRIBUTE_HANDLE 65535
#define BT_GATT_DISCOVER_PRIMARY 1
#define SPLIT_SUB_POSITION BIT(0)
#define SPLIT_SUB_SENSOR BIT(1)
#define SPLIT_SUB_RELAY_EVENT BIT(2)
#define SPLIT_SUB_BATTERY BIT(3)

typedef int bt_security_t;
typedef long atomic_t;
typedef long atomic_val_t;
enum bt_security_err { BT_SECURITY_ERR_SUCCESS, BT_SECURITY_ERR_AUTH_FAIL };
enum peripheral_slot_state {
    PERIPHERAL_SLOT_STATE_OPEN,
    PERIPHERAL_SLOT_STATE_CONNECTING,
    PERIPHERAL_SLOT_STATE_CONNECTED,
};
struct bt_conn { int security; int request_error; };
struct k_work { int unused; };
struct k_work_delayable { struct k_work work; int delay; };
struct bt_gatt_discover_params {
    void *uuid;
    void (*func)(void);
    unsigned start_handle;
    unsigned end_handle;
    unsigned type;
};
struct bt_gatt_subscribe_params {
    void *notify;
    void (*subscribe)(struct bt_conn *, uint8_t, struct bt_gatt_subscribe_params *);
    uint16_t value_handle;
    uint16_t ccc_handle;
    uint16_t value;
    atomic_t flags[1];
};
struct peripheral_slot {
    enum peripheral_slot_state state;
    struct bt_conn *conn;
    struct k_work_delayable subscribe_retry_work;
    atomic_t subscribe_retry_mask;
    uint16_t subscribe_retry_position_handle;
    uint16_t subscribe_retry_sensor_handle;
    uint16_t subscribe_retry_relay_event_handle;
    uint16_t subscribe_retry_battery_handle;
    struct bt_gatt_discover_params discover_params;
    struct bt_gatt_subscribe_params subscribe_params;
    struct bt_gatt_subscribe_params sensor_subscribe_params;
    struct bt_gatt_subscribe_params relay_event_subscribe_params;
    struct bt_gatt_subscribe_params batt_lvl_subscribe_params;
    unsigned selected_physical_layout_handle;
};
struct bt_conn_info { struct { int interval, latency, phy; } le; };

static struct peripheral_slot state;
static bool present = true;
static unsigned requested, discovered, scans, layouts, reschedules, cancels, subscribes;
static int subscribe_result;
static struct { int uuid; } split_service_uuid;
static int update_peripherals_selected_layouts_work;

static struct peripheral_slot *peripheral_slot_for_conn(struct bt_conn *conn) {
    return present && state.conn == conn ? &state : NULL;
}
static int bt_conn_get_security(struct bt_conn *conn) { return conn->security; }
static int bt_conn_set_security(struct bt_conn *conn, int level) {
    assert(level == BT_SECURITY_L2);
    requested++;
    return conn->request_error;
}
static int bt_gatt_discover(struct bt_conn *conn, void *params) {
    (void)params;
    assert(conn->security >= BT_SECURITY_L2);
    discovered++;
    return 0;
}
static void bt_conn_get_info(struct bt_conn *conn, struct bt_conn_info *info) {
    (void)conn;
    info->le.phy = 1;
}
static int bt_gatt_subscribe(struct bt_conn *conn,
                             struct bt_gatt_subscribe_params *params) {
    (void)conn;
    (void)params;
    subscribes++;
    return subscribe_result;
}
static void split_central_service_discovery_func(void) {}
static void k_work_submit(void *work) { (void)work; layouts++; }
static int k_work_reschedule(struct k_work_delayable *work, int delay) {
    (void)work;
    assert(delay == 0 || delay == 750);
    reschedules++;
    return 0;
}
static int k_work_cancel_delayable(struct k_work_delayable *work) {
    (void)work;
    cancels++;
    return 0;
}
static void atomic_set(atomic_t *target, atomic_val_t value) { *target = value; }
static atomic_val_t atomic_get(atomic_t *target) { return *target; }
static atomic_val_t atomic_or(atomic_t *target, atomic_val_t value) {
    *target |= value;
    return *target;
}
static atomic_val_t atomic_and(atomic_t *target, atomic_val_t value) {
    *target &= value;
    return *target;
}
static int start_scanning(void) { scans++; return 0; }
'''

helpers = "\n".join(
    function(patched, name)
    for name in (
        "static int split_central_subscription_bit(",
        "static uint16_t *split_central_saved_handle(",
        "static void split_central_restore_saved_handle(",
        "static void split_central_cancel_subscribe_retry(",
        "static void split_central_schedule_subscribe_retry(",
        "static void split_central_subscribe_complete(",
        "static void split_central_resume_subscribe_retries(",
    )
)

main = r'''
int main(void) {
    struct bt_conn current = {.security = 1}, stale = {.security = 2};
    state.conn = &current;
    state.state = PERIPHERAL_SLOT_STATE_CONNECTED;

    /* No GATT discovery before L2 security, then resume discovery once secured. */
    split_central_process_connection(&current);
    assert(requested == 1 && discovered == 0 && scans == 1);
    current.security = 2;
    split_central_security_changed(&current, BT_SECURITY_L2, BT_SECURITY_ERR_SUCCESS);
    assert(discovered == 1 && layouts == 0);

    state.subscribe_params.value_handle = 10;
    state.sensor_subscribe_params.value_handle = 20;
    state.relay_event_subscribe_params.value_handle = 30;
    state.relay_event_subscribe_params.ccc_handle = 31;
    state.batt_lvl_subscribe_params.value_handle = 40;

    /* Zephyr clears value_handle before the completion callback; the original
     * discovery handle must be restored so the retry can reach bt_gatt_subscribe. */
    subscribe_result = 0;
    assert(split_central_subscribe(&current, &state.relay_event_subscribe_params) == 0);
    state.relay_event_subscribe_params.value_handle = 0;
    split_central_subscribe_complete(&current, 22,
                                     &state.relay_event_subscribe_params);
    assert(state.subscribe_retry_mask == SPLIT_SUB_RELAY_EVENT);
    assert(state.relay_event_subscribe_params.value_handle == 30);
    split_central_subscribe_complete(&current, 22,
                                     &state.relay_event_subscribe_params);
    assert(state.subscribe_retry_mask == SPLIT_SUB_RELAY_EVENT);

    /* A successful completion clears the failure, and no-op retries do not subscribe. */
    subscribes = 0;
    split_central_subscribe_complete(&current, 0,
                                     &state.relay_event_subscribe_params);
    assert(state.subscribe_retry_mask == 0);
    split_central_subscribe_retry_work(&state.subscribe_retry_work.work);
    assert(subscribes == 0);

    /* Retry waits for L2 and resumes when security is established. */
    atomic_or(&state.subscribe_retry_mask, SPLIT_SUB_RELAY_EVENT);
    current.security = 1;
    split_central_subscribe_retry_work(&state.subscribe_retry_work.work);
    assert(subscribes == 0);
    current.security = 2;
    unsigned before_resume = reschedules;
    split_central_resume_subscribe_retries(&state);
    assert(reschedules == before_resume + 1);
    subscribe_result = 0;
    split_central_subscribe_retry_work(&state.subscribe_retry_work.work);
    assert(subscribes == 1);
    assert(state.relay_event_subscribe_params.subscribe ==
           split_central_subscribe_complete);

    /* Immediate subscribe errors use the same retry path. */
    state.subscribe_retry_mask = 0;
    subscribe_result = -ENOMEM;
    assert(split_central_subscribe(&current, &state.subscribe_params) == -ENOMEM);
    assert(state.subscribe_retry_mask == SPLIT_SUB_POSITION);

    /* Releasing a slot cancels the in-flight retry and clears stale failure bits. */
    before_resume = cancels;
    split_central_cancel_subscribe_retry(&state);
    assert(cancels == before_resume + 1 && state.subscribe_retry_mask == 0);

    /* A callback from an old connection cannot poison a reused slot. */
    state.conn = &current;
    unsigned after_failure = reschedules;
    split_central_subscribe_complete(&stale, 22,
                                     &state.relay_event_subscribe_params);
    assert(state.subscribe_retry_mask == 0 && reschedules == after_failure);
    split_central_subscribe_complete(NULL, 22,
                                     &state.relay_event_subscribe_params);
    assert(state.subscribe_retry_mask == 0 && reschedules == after_failure);

    /* Security errors and downgrades remain no-ops. */
    discovered = 0;
    state.subscribe_params.value_handle = 0;
    split_central_security_changed(&current, BT_SECURITY_L2, BT_SECURITY_ERR_AUTH_FAIL);
    split_central_security_changed(&current, 1, BT_SECURITY_ERR_SUCCESS);
    assert(discovered == 0);
    return 0;
}
'''

security_functions = "\n".join(
    function(patched, name)
    for name in (
        "static void split_central_process_connection(",
        "static void split_central_security_changed(",
    )
)

program = (
    prefix
    + helpers
    + "\nstatic int split_central_subscribe(struct bt_conn *conn, "
    "struct bt_gatt_subscribe_params *params);\n"
    + function(patched, "static void split_central_subscribe_retry_work(")
    + "\n"
    + function(patched, "static int split_central_subscribe(")
    + "\n"
    + security_functions
    + main
)

with tempfile.TemporaryDirectory() as directory:
    cfile = Path(directory) / "test.c"
    binary = Path(directory) / "test"
    cfile.write_text(program)
    subprocess.run(
        [
            "cc",
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=address,undefined",
            str(cfile),
            "-o",
            str(binary),
        ],
        check=True,
    )
    subprocess.run([str(binary)], check=True)

print(
    "Split security: encryption gate, CCC completion, delayed retry, "
    "security resume, stale callbacks and slot cleanup passed"
)
