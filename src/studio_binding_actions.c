/* SPDX-License-Identifier: MIT */
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/retention/bootmode.h>
#include <zephyr/settings/settings.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/reboot.h>
#include <dt-bindings/zmk/bt.h>
#include <zmk/behavior.h>

LOG_MODULE_REGISTER(velvet_studio_actions, LOG_LEVEL_INF);
enum { ACTION_NONE, ACTION_BOOTLOADER, ACTION_CLEAR_BONDS };
static atomic_t pending_action;

static void perform_action(struct k_work *work) {
    ARG_UNUSED(work);
    int action = atomic_get(&pending_action);
    int err;
    if (action == ACTION_BOOTLOADER) {
        err = bootmode_set(BOOT_MODE_TYPE_BOOTLOADER);
        if (err == 0) {
            sys_reboot(SYS_REBOOT_WARM);
        }
        LOG_ERR("Bootloader request failed: %d", err);
    } else if (action == ACTION_CLEAR_BONDS) {
        err = bt_unpair(BT_ID_DEFAULT, NULL);
        if (err < 0) {
            LOG_ERR("Unpair failed: %d", err);
            atomic_clear(&pending_action);
            return;
        }
        /* Clear saved host profiles and split-central peer slots, then reboot
         * to discard the corresponding live state without rewriting old peers. */
        for (int i = 0; i < CONFIG_BT_MAX_PAIRED; i++) {
            char key[40];
            snprintf(key, sizeof(key), "ble/profiles/%d", i);
            err = settings_delete(key);
            if (err < 0) {
                LOG_ERR("Delete %s failed: %d", key, err);
                atomic_clear(&pending_action);
                return;
            }
        }
        for (int i = 0; i < CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS; i++) {
            char key[40];
            snprintf(key, sizeof(key), "ble/peripheral_addresses/%d", i);
            err = settings_delete(key);
            if (err < 0) {
                LOG_ERR("Delete %s failed: %d", key, err);
                atomic_clear(&pending_action);
                return;
            }
        }
        sys_reboot(SYS_REBOOT_WARM);
    }
    atomic_clear(&pending_action);
}
K_WORK_DELAYABLE_DEFINE(action_work, perform_action);

int velvet_studio_binding_action(const struct zmk_behavior_binding *binding) {
    if (!binding->behavior_dev) {
        return 0;
    }
    int action = ACTION_NONE;
    if (strcmp(binding->behavior_dev, "bootload") == 0) {
        action = ACTION_BOOTLOADER;
    } else if (strcmp(binding->behavior_dev, "bluetooth") == 0 &&
               binding->param1 == BT_CLR_ALL_CMD) {
        action = ACTION_CLEAR_BONDS;
    }
    if (action == ACTION_NONE) {
        return 0;
    }
    if (!atomic_cas(&pending_action, ACTION_NONE, action)) {
        return -EBUSY;
    }
    /* Let Studio transmit its response before USB disappears. The operation
     * consumes the edit: do not persist an administrative action as a key. */
    int ret = k_work_reschedule(&action_work, K_MSEC(500));
    if (ret < 0) {
        atomic_clear(&pending_action);
        return ret;
    }
    return 1;
}
