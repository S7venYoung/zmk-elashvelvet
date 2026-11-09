#include <string.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gap.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>
#include "../dual-mode/link.h"

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#if IS_ENABLED(CONFIG_SHIELD_VELVET_DUAL_HOST)

static const struct bt_data beacon_data[] = {
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, VELVET_RIGHT_BEACON_UUID),
};
static struct bt_le_ext_adv *beacon;

void velvet_dual_link_start(void) {
    int err = bt_le_ext_adv_create(
        BT_LE_ADV_PARAM(BT_LE_ADV_OPT_EXT_ADV | BT_LE_ADV_OPT_USE_IDENTITY, 160, 240, NULL),
        NULL, &beacon);
    if (!err) {
        err = bt_le_ext_adv_set_data(beacon, beacon_data, ARRAY_SIZE(beacon_data), NULL, 0);
    }
    if (!err) {
        err = bt_le_ext_adv_start(beacon, BT_LE_EXT_ADV_START_DEFAULT);
    }
    if (err) {
        LOG_ERR("Cannot advertise the right-hand host (%d)", err);
    }
}

#else

#define RIGHT_PEER_TIMEOUT_MS 5500

extern void velvet_dual_left_select_identity(uint8_t identity);
extern bool zmk_split_bt_peripheral_is_connected(void);

static bt_addr_le_t right_peer;
static struct k_spinlock peer_lock;
static uint8_t right_identity;
static atomic_t using_right;
static atomic_t last_seen;
static atomic_t seen;

bool velvet_dual_left_is_right_host(void) { return atomic_get(&using_right) != 0; }

static void find_right_peer(const struct bt_bond_info *info, void *data) {
    bt_addr_le_copy(data, &info->addr);
}

struct beacon_match {
    bool found;
};

static bool match_beacon(struct bt_data *data, void *context) {
    static const uint8_t uuid[] = {VELVET_RIGHT_BEACON_UUID};
    if (data->type == BT_DATA_UUID128_ALL && data->data_len == sizeof(uuid) &&
        memcmp(data->data, uuid, sizeof(uuid)) == 0) {
        ((struct beacon_match *)context)->found = true;
        return false;
    }
    return true;
}

static void scan_report(const bt_addr_le_t *address, int8_t rssi, uint8_t type,
                        struct net_buf_simple *data) {
    ARG_UNUSED(rssi);
    ARG_UNUSED(type);
    struct beacon_match match = {0};
    bt_data_parse(data, match_beacon, &match);
    if (!match.found) {
        return;
    }
    k_spinlock_key_t key = k_spin_lock(&peer_lock);
    bool allowed = bt_addr_le_eq(&right_peer, BT_ADDR_LE_NONE) ||
                   bt_addr_le_eq(address, &right_peer);
    k_spin_unlock(&peer_lock, key);
    if (!allowed) {
        return;
    }
    atomic_set(&last_seen, k_uptime_get_32());
    atomic_set(&seen, 1);
}

static void select_host(struct k_work *work) {
    bt_addr_le_t peer = bt_addr_le_none;
    bt_foreach_bond(right_identity, find_right_peer, &peer);
    k_spinlock_key_t key = k_spin_lock(&peer_lock);
    right_peer = peer;
    k_spin_unlock(&peer_lock, key);
    const bool right_present = atomic_get(&seen) &&
        (uint32_t)(k_uptime_get_32() - (uint32_t)atomic_get(&last_seen)) < RIGHT_PEER_TIMEOUT_MS;
    if (right_present && !velvet_dual_left_is_right_host()) {
        atomic_set(&using_right, 1);
        velvet_dual_left_select_identity(right_identity);
    } else if (!right_present && velvet_dual_left_is_right_host() &&
               !zmk_split_bt_peripheral_is_connected()) {
        atomic_clear(&using_right);
        velvet_dual_left_select_identity(BT_ID_DEFAULT);
    }

    k_work_reschedule(k_work_delayable_from_work(work), K_MSEC(250));
}

K_WORK_DELAYABLE_DEFINE(host_selection_work, select_host);

void velvet_dual_link_start(void) {
    bt_addr_le_t identities[2];
    size_t count = ARRAY_SIZE(identities);
    bt_id_get(identities, &count);
    int identity = count > 1 ? 1 : bt_id_create(NULL, NULL);
    if (identity <= 0) {
        LOG_ERR("Cannot create the right-hand split identity (%d)", identity);
        return;
    }
    right_identity = (uint8_t)identity;
    bt_addr_le_copy(&right_peer, BT_ADDR_LE_NONE);
    bt_foreach_bond(right_identity, find_right_peer, &right_peer);

    /* Repeated reports keep the lease alive. Use a low-duty passive window. */
    int err = bt_le_scan_start(BT_LE_SCAN_PARAM(BT_LE_SCAN_TYPE_PASSIVE, 0, 400, 64),
                               scan_report);
    if (err) {
        LOG_ERR("Cannot watch for the right-hand host (%d)", err);
        return;
    }
    k_work_schedule(&host_selection_work, K_NO_WAIT);
}
#endif
