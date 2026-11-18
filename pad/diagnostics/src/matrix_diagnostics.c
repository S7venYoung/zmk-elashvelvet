/* SPDX-License-Identifier: MIT */
#include <string.h>
#include <errno.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/kscan.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/byteorder.h>
#include <hal/nrf_gpio.h>
#include <zmk/keymap.h>
#include <zmk/physical_layouts.h>
#include <zmk/studio/custom.h>
#include <pb_encode.h>

/* Operation 1 is read-only. Test-only operation 2 is explicitly gated below. */
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


#if IS_ENABLED(CONFIG_PAD_MATRIX_SETTLED_PROBE)
#define MATRIX_NODE DT_NODELABEL(pad_matrix)
#if DT_ENUM_IDX(MATRIX_NODE, diode_direction) == 0
#define OUTPUT_PROP row_gpios
#define INPUT_PROP col_gpios
#else
#define OUTPUT_PROP col_gpios
#define INPUT_PROP row_gpios
#endif
#define MATRIX_SPEC(node, prop, idx) GPIO_DT_SPEC_GET_BY_IDX(node, prop, idx),
static const struct gpio_dt_spec probe_outputs[] = {
    DT_FOREACH_PROP_ELEM(MATRIX_NODE, OUTPUT_PROP, MATRIX_SPEC)};
static const struct gpio_dt_spec probe_inputs[] = {
    DT_FOREACH_PROP_ELEM(MATRIX_NODE, INPUT_PROP, MATRIX_SPEC)};
BUILD_ASSERT(ARRAY_SIZE(probe_outputs) == 4 && ARRAY_SIZE(probe_inputs) == 4);

static int input_mask(void) {
    int mask = 0;
    for (unsigned i = 0; i < ARRAY_SIZE(probe_inputs); i++) {
        int value = gpio_pin_get_dt(&probe_inputs[i]);
        if (value < 0) return value;
        if (value) mask |= BIT(i);
    }
    return mask;
}

static int settled_probe(uint8_t levels[5], int *resume_result) {
    const struct device *dev = DEVICE_DT_GET(MATRIX_NODE);
    *resume_result = 0;
    if (!device_is_ready(dev)) return -ENODEV;
    int ret = kscan_disable_callback(dev);
    if (ret < 0) {
        *resume_result = kscan_enable_callback(dev);
        return ret;
    }
    for (unsigned i = 0; i < ARRAY_SIZE(probe_outputs); i++) {
        ret = gpio_pin_set_dt(&probe_outputs[i], 0);
        if (ret < 0) goto restore;
    }
    k_msleep(5);
    ret = input_mask();
    if (ret < 0) goto restore;
    levels[0] = ret;
    for (unsigned i = 0; i < ARRAY_SIZE(probe_outputs); i++) {
        ret = gpio_pin_set_dt(&probe_outputs[i], 1);
        if (ret < 0) goto restore;
        k_msleep(5);
        ret = input_mask();
        if (ret < 0) goto restore;
        levels[i + 1] = ret;
        ret = gpio_pin_set_dt(&probe_outputs[i], 0);
        if (ret < 0) goto restore;
        k_msleep(5);
    }
    ret = 0;
restore:
    for (unsigned i = 0; i < ARRAY_SIZE(probe_outputs); i++) {
        int err = gpio_pin_set_dt(&probe_outputs[i], 0);
        if (!ret && err < 0) ret = err;
    }
    *resume_result = kscan_enable_callback(dev);
    return ret;
}
#endif

static bool read_snapshot(const zmk_custom_CallRequest *req, pb_callback_t *res) {
    if (req->payload.size != 2 || req->payload.bytes[0] != 8 ||
        (req->payload.bytes[1] != 1 &&
         !(IS_ENABLED(CONFIG_PAD_MATRIX_SETTLED_PROBE) && req->payload.bytes[1] == 2))) {
        return false;
    }
    memset(snapshot, 0, sizeof(snapshot));
    snapshot[0] = 1;
#if IS_ENABLED(CONFIG_PAD_MATRIX_SETTLED_PROBE)
    if (req->payload.bytes[1] == 2) {
        int resumed;
        int result = settled_probe(snapshot + 78, &resumed);
        snapshot[76] = 2;
        sys_put_le32((uint32_t)result, snapshot + 84);
        sys_put_le32((uint32_t)resumed, snapshot + 88);
    }
#endif
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
