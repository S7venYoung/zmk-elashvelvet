#include <zephyr/drivers/flash.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/sys/reboot.h>
#include "../dual-mode/layout.h"

#if IS_ENABLED(CONFIG_SHIELD_VELVET_DUAL_HOST)
#include <zmk/endpoints.h>
#endif

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#define CHORD_MASK (BIT(0) | BIT(5))
#define HOLD_MS 2000

static void switch_image(struct k_work *work) {
    ARG_UNUSED(work);
    if (IS_ENABLED(CONFIG_SHIELD_VELVET_HOST_DIAGNOSTIC)) {
        return;
    }
    const struct device *flash = FIXED_PARTITION_DEVICE(code_partition);
    const uint32_t mode = IS_ENABLED(CONFIG_SHIELD_VELVET_DUAL_HOST)
                              ? VELVET_MODE_NANO : VELVET_MODE_HOST;
    if (!device_is_ready(flash)) {
        LOG_ERR("Cannot store right-hand mode: flash unavailable");
        return;
    }

    off_t offset;
    int err;
    for (offset = VELVET_MODE_START; offset < VELVET_SETTINGS_START; offset += sizeof(mode)) {
        uint32_t value;
        err = flash_read(flash, offset, &value, sizeof(value));
        if (err) {
            goto failed;
        }
        if (value == UINT32_MAX) {
            break;
        }
    }
    if (offset == VELVET_SETTINGS_START) {
        err = flash_erase(flash, VELVET_MODE_START, VELVET_PAGE_SIZE);
        if (err) {
            goto failed;
        }
        offset = VELVET_MODE_START;
    }
    err = flash_write(flash, offset, &mode, sizeof(mode));
    if (err) {
        goto failed;
    }

#if IS_ENABLED(CONFIG_SHIELD_VELVET_DUAL_HOST)
    zmk_endpoint_clear_reports();
#endif
    sys_reboot(SYS_REBOOT_COLD);

failed:
    LOG_ERR("Cannot store right-hand mode (%d)", err);
}

K_WORK_DELAYABLE_DEFINE(mode_switch_work, switch_image);

/* Called before mapping, on the same work queue as the normal matrix events. */
void velvet_dual_right_matrix(uint32_t row, uint32_t column, bool pressed) {
    static uint32_t held;
    static int64_t chord_since;
    static bool switch_pending;
    if (row >= 5 || column >= 6) {
        return;
    }

    const uint32_t before = held;
    WRITE_BIT(held, row * 6 + column, pressed);
    if (held == CHORD_MASK) {
        if (before != CHORD_MASK) {
            chord_since = k_uptime_get();
        }
    } else if (before == CHORD_MASK && !pressed && k_uptime_get() - chord_since >= HOLD_MS) {
        switch_pending = true;
    }

    if (pressed) {
        k_work_cancel_delayable(&mode_switch_work);
    }
    if (!held && switch_pending) {
        switch_pending = false;
        k_work_schedule(&mode_switch_work, K_MSEC(100));
    }
}
