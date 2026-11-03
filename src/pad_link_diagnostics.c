/* SPDX-License-Identifier: MIT */
#include <zephyr/kernel.h>
#include <zephyr/init.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>
LOG_MODULE_REGISTER(pad_link_diagnostics, LOG_LEVEL_INF);

/* Non-mutating slot lookup exported by the pinned ZMK split central. */
extern int peripheral_slot_index_for_conn(struct bt_conn *conn);

static void inspect_connection(struct bt_conn *conn, void *context) {
    uint32_t *mask = context;
    struct bt_conn_info info;
    if (bt_conn_get_info(conn, &info) != 0 || info.type != BT_CONN_TYPE_LE ||
        info.role != BT_CONN_ROLE_CENTRAL) {
        return;
    }
    int slot = peripheral_slot_index_for_conn(conn);
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
