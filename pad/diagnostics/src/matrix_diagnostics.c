/* SPDX-License-Identifier: MIT */
#include <string.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/byteorder.h>
#include <hal/nrf_gpio.h>
#include <zmk/keymap.h>
#include <zmk/physical_layouts.h>
#include <zmk/studio/custom.h>
#include <pb_encode.h>

/* Snapshots only. Never reconfigure GPIOs, stop the scanner or inject keys. */
static uint8_t snapshot[96];
static struct zmk_rpc_custom_subsystem_meta meta = {
    ZMK_RPC_CUSTOM_SUBSYSTEM_UI_URLS(),
    .security = ZMK_STUDIO_RPC_HANDLER_UNSECURED,
};

static bool encode_snapshot(pb_ostream_t *stream, const pb_field_t *field,
                            void *const *arg) {
    ARG_UNUSED(arg);
    return pb_encode_tag_for_field(stream, field) &&
           pb_encode_varint(stream, sizeof(snapshot) + 2) &&
           pb_encode_tag(stream, PB_WT_STRING, 1) &&
           pb_encode_string(stream, snapshot, sizeof(snapshot));
}

static bool read_snapshot(const zmk_custom_CallRequest *req, pb_callback_t *res) {
    if (req->payload.size != 2 || req->payload.bytes[0] != 8 ||
        req->payload.bytes[1] != 1) {
        return false;
    }
    memset(snapshot, 0, sizeof(snapshot));
    snapshot[0] = 1;
    snapshot[1] = device_is_ready(DEVICE_DT_GET(DT_NODELABEL(pad_matrix)));
    snapshot[2] = (uint8_t)zmk_physical_layouts_get_selected();
    snapshot[3] = zmk_keymap_layer_default();
    sys_put_le32(zmk_keymap_layer_state() | BIT(snapshot[3]), snapshot + 4);
    sys_put_le32(k_uptime_get_32(), snapshot + 8);
    sys_put_le32(NRF_P0->IN, snapshot + 12);
    sys_put_le32(NRF_P0->OUT, snapshot + 16);
    sys_put_le32(NRF_P0->DIR, snapshot + 20);
    sys_put_le32(NRF_P1->IN, snapshot + 24);
    sys_put_le32(NRF_P1->OUT, snapshot + 28);
    sys_put_le32(NRF_P1->DIR, snapshot + 32);
    /* Author-provided rows followed by columns; actual PIN_CNF includes SENSE. */
    NRF_GPIO_Type *const ports[8] = {NRF_P1, NRF_P1, NRF_P0, NRF_P0,
                                     NRF_P0, NRF_P0, NRF_P0, NRF_P1};
    const uint8_t pins[8] = {13, 15, 2, 29, 20, 22, 24, 0};
    for (unsigned int i = 0; i < 8; i++) {
        sys_put_le32(ports[i]->PIN_CNF[pins[i]], snapshot + 36 + i * 4);
        snapshot[68 + i] = (ports[i]->IN >> pins[i]) & 1;
    }
    res->funcs.encode = encode_snapshot;
    res->arg = NULL;
    return true;
}
ZMK_RPC_CUSTOM_SUBSYSTEM(pad_matrix_diag, &meta, read_snapshot);
