/* SPDX-License-Identifier: MIT */
#include <errno.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/sys/reboot.h>
#include <zephyr/retention/bootmode.h>
#include <zephyr/logging/log.h>
#include <zmk/studio/custom.h>
#include <zmk/behavior.h>
#include <drivers/behavior.h>
#include <dt-bindings/zmk/rgb.h>
#include <pb_encode.h>
#include "../policy.h"
#if CONFIG_PAD_DUAL_IMAGE_SLOT == 0
#include <zmk/endpoints.h>
#endif
LOG_MODULE_REGISTER(pad_dual, CONFIG_ZMK_LOG_LEVEL);
BUILD_ASSERT(FIXED_PARTITION_OFFSET(pad_dual_mode) == PAD_MODE_JOURNAL);
BUILD_ASSERT(FIXED_PARTITION_OFFSET(code_partition) ==
             (CONFIG_PAD_DUAL_IMAGE_SLOT ? PAD_SLOT_B_START : PAD_SLOT_A_START));
BUILD_ASSERT(FIXED_PARTITION_SIZE(pad_dual_mode) == PAD_PAGE_SIZE);
BUILD_ASSERT(FIXED_PARTITION_SIZE(storage_partition) == 0x8000);
BUILD_ASSERT(FIXED_PARTITION_OFFSET(storage_partition) ==
             (CONFIG_PAD_DUAL_IMAGE_SLOT ? PAD_SLOT_B_NVS : PAD_SLOT_A_NVS));
static int action, last_error;
static uint8_t response[16];
static struct pad_chord_state chord;
static uint32_t consumed;
static bool pending_bl;
static bool image_ready(unsigned mode) {
    const struct pad_image_table *t = (const void *)PAD_SELECTOR_META;
    if (t->magic != PAD_META_MAGIC || t->version != 1 || t->count != 2) return false;
    const struct pad_image_descriptor *d = &t->image[mode];
    uint32_t base = mode ? PAD_SLOT_B_START : PAD_SLOT_A_START;
    uint32_t end = mode ? PAD_SLOT_B_LIMIT : PAD_SLOT_A_LIMIT;
    if (d->mode != mode || d->base != base || d->length < 8 || d->length > end - base) return false;
    const uint32_t *v = (const void *)base;
    return pad_vector_valid(v[0], v[1], base, base + d->length) &&
           pad_crc32((const void *)base, d->length) == d->crc;
}
static int store_mode(unsigned mode) {
    const struct device *flash = FIXED_PARTITION_DEVICE(pad_dual_mode);
    if (!device_is_ready(flash)) return -ENODEV;
    uint32_t record[2] = {PAD_MODE_MAGIC | mode, ~(PAD_MODE_MAGIC | mode)};
    uint32_t old[2]; off_t at;
    for (at = PAD_MODE_JOURNAL; at < PAD_MODE_JOURNAL + PAD_PAGE_SIZE; at += 8) {
        int err = flash_read(flash, at, old, sizeof(old));
        if (err) return err;
        if (old[0] == UINT32_MAX && old[1] == UINT32_MAX) break;
    }
    if (at == PAD_MODE_JOURNAL + PAD_PAGE_SIZE) {
        int err = flash_erase(flash, PAD_MODE_JOURNAL, PAD_PAGE_SIZE);
        if (err) return err;
        at = PAD_MODE_JOURNAL;
    }
    int err = flash_write(flash, at, record, sizeof(record));
    if (err) return err;
    err = flash_read(flash, at, old, sizeof(old));
    return err ? err : memcmp(old, record, sizeof(old)) ? -EIO : 0;
}
static void perform_action(struct k_work *work) {
    ARG_UNUSED(work);
    int err;
    if (action == 2) {
        err = bootmode_set(BOOT_MODE_TYPE_BOOTLOADER);
    } else {
        unsigned next = CONFIG_PAD_DUAL_IMAGE_SLOT ^ 1;
        err = image_ready(next) ? store_mode(next) : -ENOEXEC;
    }
    last_error = err;
    if (err) { LOG_ERR("Mode/boot request failed: %d", err); return; }
#if CONFIG_PAD_DUAL_IMAGE_SLOT == 0
    zmk_endpoint_clear_reports();
#endif
    sys_reboot(SYS_REBOOT_COLD);
}
K_WORK_DELAYABLE_DEFINE(action_work, perform_action);
static void schedule_action(int requested) {
    action = requested;
    k_work_reschedule(&action_work, K_MSEC(100));
}
#if CONFIG_PAD_DUAL_IMAGE_SLOT == 1
static int local_rgb_command(unsigned p) {
    switch (p) {
    case 6: return RGB_TOG_CMD;
    case 7: return RGB_EFF_CMD;
    case 8: return RGB_BRI_CMD;
    case 9: return RGB_BRD_CMD;
    default: return -1;
    }
}
#endif
/* Hooked before the normal local physical-layout event, so it works offline. */
bool pad_dual_matrix_event(uint32_t row, uint32_t col, bool pressed) {
    if (row >= 4 || col >= 4) return false;
    unsigned p = row * 4 + col; bool toggle;
    if (pressed) k_work_cancel_delayable(&action_work);
    bool swallow = pad_chord_event(&chord, p, pressed, k_uptime_get(), &toggle);
#if CONFIG_PAD_DUAL_IMAGE_SLOT == 1
    int rgb = local_rgb_command(p);
    if (pressed && (chord.held & BIT(12)) && (rgb >= 0 || p == 11)) {
        consumed |= BIT(p);
        if (p == 11) pending_bl = true;
        else {
            struct zmk_behavior_binding binding = {
                .behavior_dev = DEVICE_DT_NAME(DT_NODELABEL(rgb_ug)), .param1 = rgb,
            };
            struct zmk_behavior_binding_event event = {.position = p, .timestamp = k_uptime_get()};
            behavior_keymap_binding_pressed(&binding, event);
        }
    }
#endif
    if (consumed & BIT(p)) { swallow = true; if (!pressed) consumed &= ~BIT(p); }
    if (!chord.held && pending_bl) { pending_bl = false; schedule_action(2); }
    else if (toggle) schedule_action(1);
    return swallow;
}
static bool encode_info(pb_ostream_t *s, const pb_field_t *f, void *const *arg) {
    ARG_UNUSED(arg);
    return pb_encode_tag_for_field(s, f) && pb_encode_varint(s, sizeof(response) + 2) &&
           pb_encode_tag(s, PB_WT_STRING, 1) && pb_encode_string(s, response, sizeof(response));
}
static bool mode_rpc(const zmk_custom_CallRequest *req, pb_callback_t *res) {
    if (req->payload.size != 2 || req->payload.bytes[0] != 8 ||
        (req->payload.bytes[1] != 1 && req->payload.bytes[1] != 2)) return false;
    if (req->payload.bytes[1] == 2) schedule_action(1);
    memset(response, 0, sizeof(response)); response[0] = 1;
    response[1] = CONFIG_PAD_DUAL_IMAGE_SLOT;
    response[2] = pad_read_mode((const void *)PAD_MODE_JOURNAL, PAD_PAGE_SIZE / 4);
    sys_put_le32((uint32_t)last_error, response + 4);
    sys_put_le32(k_uptime_get_32(), response + 8);
    res->funcs.encode = encode_info; res->arg = NULL; return true;
}
static struct zmk_rpc_custom_subsystem_meta meta = {
    ZMK_RPC_CUSTOM_SUBSYSTEM_UI_URLS(), .security = ZMK_STUDIO_RPC_HANDLER_UNSECURED,
};
ZMK_RPC_CUSTOM_SUBSYSTEM(pad_dual_mode, &meta, mode_rpc);
