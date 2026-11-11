/* SPDX-License-Identifier: MIT */
#include <zephyr/kernel.h>
#include <zephyr/init.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>
LOG_MODULE_REGISTER(pad_link_diagnostics, LOG_LEVEL_INF);

/* Non-mutating slot lookup exported by the pinned ZMK split central. */
extern int peripheral_slot_index_for_conn(struct bt_conn *conn);

extern int eyelash_diagnostic_scan_state(void);

static uint32_t reached_stages;
static const char *settings_handler = "none";
static int settings_phase, settings_result;

void eyelash_diagnostic_settings(const char *name, int phase, int result) {
    settings_handler = name;
    settings_phase = phase;
    settings_result = result;
}

/* Stage 1: slot reservation; 2: stop scan; 3: create; 4: start scan. */
void eyelash_diagnostic_stage(unsigned stage, int result) {
    static int previous[16];
    static uint32_t last[16];
    uint32_t now = k_uptime_get_32();
    if (stage >= ARRAY_SIZE(last)) { return; }
    if (last[stage] && previous[stage] == result && now - last[stage] < 1000) { return; }
    reached_stages |= BIT(stage);
    previous[stage] = result;
    last[stage] = now ? now : 1;
    LOG_INF("PAD_TRACE stage=%u result=%d", stage, result);
}

static bool is_split_central_connection(struct bt_conn *conn) {
    struct bt_conn_info info;
    return bt_conn_get_info(conn, &info) == 0 && info.type == BT_CONN_TYPE_LE &&
           info.role == BT_CONN_ROLE_CENTRAL;
}

static void trace_connected(struct bt_conn *conn, uint8_t err) {
    if (!is_split_central_connection(conn)) { return; }
    LOG_INF("PAD_TRACE connected hci_error=%u slot=%d",
            (unsigned)err, peripheral_slot_index_for_conn(conn));
}
static void trace_disconnected(struct bt_conn *conn, uint8_t reason) {
    if (!is_split_central_connection(conn)) { return; }
    LOG_INF("PAD_TRACE disconnected hci_reason=%u", (unsigned)reason);
}
static void trace_security(struct bt_conn *conn, bt_security_t level, enum bt_security_err err) {
    if (!is_split_central_connection(conn)) { return; }
    LOG_INF("PAD_TRACE security level=%u error=%u", (unsigned)level, (unsigned)err);
}
BT_CONN_CB_DEFINE(eyelash_diagnostic_callbacks) = {
    .connected = trace_connected,
    .disconnected = trace_disconnected,
    .security_changed = trace_security,
};

static void inspect_connection(struct bt_conn *conn, void *context) {
    uint32_t *mask = context;
    struct bt_conn_info info;
    if (bt_conn_get_info(conn, &info) != 0 || info.type != BT_CONN_TYPE_LE ||
        info.role != BT_CONN_ROLE_CENTRAL) {
        return;
    }
    int slot = peripheral_slot_index_for_conn(conn);
    LOG_INF("PAD_TRACE central_connection slot=%d state=%u security=%u",
            slot, (unsigned)info.state, (unsigned)bt_conn_get_security(conn));
    if (slot < 0 || slot >= CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS) {
        return;
    }
    if (info.state == BT_CONN_STATE_CONNECTED) {
        *mask |= BIT(slot);
    }
    LOG_INF("PAD_LINK slot=%d state=%u security=%u", slot, (unsigned)info.state,
            (unsigned)bt_conn_get_security(conn));
}

static void snapshot(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(snapshot_work, snapshot);
static void snapshot(struct k_work *work) {
    ARG_UNUSED(work);
    uint32_t mask = 0;
    LOG_INF("PAD_TRACE scan_flags=%d (enabled=1 scan=2 loaded=4 callback=8)",
            eyelash_diagnostic_scan_state());
    LOG_INF("PAD_INIT stages=0x%x handler=%s phase=%d result=%d",
            (unsigned)reached_stages, settings_handler, settings_phase, settings_result);
    bt_conn_foreach(BT_CONN_TYPE_LE, inspect_connection, &mask);
    LOG_INF("PAD_LINK configured_slots=%u connected_mask=0x%02x",
            (unsigned)CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS, (unsigned)mask);
    k_work_reschedule(&snapshot_work, K_SECONDS(5));
}
static int diagnostics_init(void) {
    k_work_reschedule(&snapshot_work, K_SECONDS(5));
    return 0;
}
SYS_INIT(diagnostics_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
