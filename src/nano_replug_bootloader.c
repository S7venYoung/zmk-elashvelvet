/*
 * Copyright (c) 2026 S7venYoung
 * SPDX-License-Identifier: MIT
 */

#include <errno.h>
#include <string.h>

#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/retention/bootmode.h>
#include <zephyr/settings/settings.h>
#include <zephyr/sys/reboot.h>
#include <zephyr/logging/log.h>

#include <zmk/usb.h>

LOG_MODULE_REGISTER(velvet_nano_replug, LOG_LEVEL_INF);

#define REPLUG_SETTING "velvet_nano_replug/stage"
#define REPLUG_SUBTREE "velvet_nano_replug"
#define REPLUG_ARM_DELAY K_MSEC(1200)
#define REPLUG_WINDOW K_SECONDS(10)

static void check_replug(struct k_work *work);
static void clear_replug(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(check_work, check_replug);
K_WORK_DELAYABLE_DEFINE(clear_work, clear_replug);

static int read_stage(const char *key, size_t len, settings_read_cb read_cb, void *cb_arg,
                      void *param) {
    uint8_t *stage = param;

    if (strcmp(key, "stage") != 0 || len != sizeof(*stage)) {
        return 0;
    }

    return read_cb(cb_arg, stage, sizeof(*stage)) == sizeof(*stage) ? 0 : -EIO;
}

static void clear_replug(struct k_work *work) {
    ARG_UNUSED(work);
    int err = settings_delete(REPLUG_SETTING);
    if (err < 0) {
        LOG_ERR("Failed to clear USB replug stage: %d", err);
    }
}

static void check_replug(struct k_work *work) {
    ARG_UNUSED(work);
    if (zmk_usb_get_conn_state() != ZMK_USB_CONN_HID) {
        k_work_reschedule(&check_work, K_MSEC(250));
        return;
    }

    uint8_t stage = 0;
    int err = settings_load_subtree_direct(REPLUG_SUBTREE, read_stage, &stage);
    if (err < 0) {
        LOG_ERR("Failed to read USB replug stage: %d", err);
        return;
    }

    if (stage >= 2) {
        /* Delete first so a failed bootloader entry cannot create a loop. */
        err = settings_delete(REPLUG_SETTING);
        if (err < 0) {
            LOG_ERR("Failed to clear USB replug stage: %d", err);
            return;
        }
        err = bootmode_set(BOOT_MODE_TYPE_BOOTLOADER);
        if (err < 0) {
            LOG_ERR("Failed to request bootloader: %d", err);
            return;
        }
        sys_reboot(SYS_REBOOT_WARM);
    }

    stage++;
    err = settings_save_one(REPLUG_SETTING, &stage, sizeof(stage));
    if (err < 0) {
        LOG_ERR("Failed to save USB replug stage: %d", err);
        return;
    }
    k_work_reschedule(&clear_work, REPLUG_WINDOW);
}

static int nano_replug_init(void) {
    k_work_reschedule(&check_work, REPLUG_ARM_DELAY);
    return 0;
}

SYS_INIT(nano_replug_init, APPLICATION, 97);
