"""Pad-only local switching and peripheral position offset hooks."""
from pathlib import Path
import sys

def replace(path, old, new, marker):
    text = path.read_text()
    if marker in text: return
    if text.count(old) != 1: raise ValueError(f'Unexpected ZMK anchor: {path}: {old}')
    path.write_text(text.replace(old, new, 1))

def patch(app):
    app = Path(app)
    anchor = '        bool pressed = (ev.state == ZMK_KSCAN_EVENT_STATE_PRESSED);'
    replace(app / 'src/physical_layouts.c', anchor, anchor + '''
#if IS_ENABLED(CONFIG_PAD_DUAL_IMAGE)
        extern bool pad_dual_matrix_event(uint32_t row, uint32_t col, bool pressed);
        if (pad_dual_matrix_event(ev.row, ev.column, pressed)) continue;
#endif
''', 'pad_dual_matrix_event')
    replace(app / 'src/split/peripheral.c', '.position = pos_ev->position,', '''.position = pos_ev->position
#if IS_ENABLED(CONFIG_PAD_DUAL_IMAGE)
                             + CONFIG_PAD_DUAL_RECEIVER_OFFSET
#endif
                             ,''', 'CONFIG_PAD_DUAL_RECEIVER_OFFSET')
    replace(app / 'src/split/bluetooth/service.c',
            'static uint8_t num_of_positions = ZMK_KEYMAP_LEN;', '''#if IS_ENABLED(CONFIG_PAD_DUAL_IMAGE)
BUILD_ASSERT(ZMK_KEYMAP_LEN + CONFIG_PAD_DUAL_RECEIVER_OFFSET <= POS_STATE_LEN * 8);
static uint8_t num_of_positions = ZMK_KEYMAP_LEN + CONFIG_PAD_DUAL_RECEIVER_OFFSET;
#else
static uint8_t num_of_positions = ZMK_KEYMAP_LEN;
#endif''', 'CONFIG_PAD_DUAL_RECEIVER_OFFSET')
    replace(app / 'src/split/bluetooth/peripheral.c',
            '    bt_foreach_bond(BT_ID_DEFAULT, each_bond, &central_addr);',
            """    uint8_t pad_identity = BT_ID_DEFAULT;
#if IS_ENABLED(CONFIG_PAD_DUAL_IMAGE)
    /* Identity 1 has a generated static address, distinct from standalone ID 0. */
    size_t identities = 0;
    bt_id_get(NULL, &identities);
    if (identities < 2) {
        int created = bt_id_create(NULL, NULL);
        if (created < 0) return created;
        bt_id_get(NULL, &identities);
        if (identities < 2) return -ENOMEM;
    }
    pad_identity = 1;
#endif
    bt_foreach_bond(pad_identity, each_bond, &central_addr);""", 'pad_identity')
    replace(app / 'src/split/bluetooth/peripheral.c',
            '        return bt_le_adv_start(&adv_param, NULL, 0, NULL, 0);',
            '        adv_param.id = pad_identity; /* PAD_DUAL_ADV_ID */\n'
            '        return bt_le_adv_start(&adv_param, NULL, 0, NULL, 0);', 'PAD_DUAL_ADV_ID')
    replace(app / 'src/split/bluetooth/peripheral.c',
            '        return bt_le_adv_start(BT_LE_ADV_CONN_FAST_2, zmk_ble_ad, ARRAY_SIZE(zmk_ble_ad), NULL, 0);',
            '        struct bt_le_adv_param param = *BT_LE_ADV_CONN_FAST_2;\n'
            '        param.id = pad_identity; /* PAD_DUAL_UNBONDED_ID */\n'
            '        return bt_le_adv_start(&param, zmk_ble_ad, ARRAY_SIZE(zmk_ble_ad), NULL, 0);',
            'PAD_DUAL_UNBONDED_ID')
    replace(app / 'src/studio/CMakeLists.txt',
            'target_sources(app PRIVATE keymap_subsystem.c)',
            'if(NOT CONFIG_PAD_DUAL_IMAGE OR NOT CONFIG_ZMK_SPLIT OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL)\n'
            '  target_sources(app PRIVATE keymap_subsystem.c)\n'
            'endif() # PAD_DUAL_PERIPHERAL_RPC\n', 'PAD_DUAL_PERIPHERAL_RPC')
    # A split peripheral has no host HID endpoints. Keep Studio on USB CDC.
    only_host = '!IS_ENABLED(CONFIG_PAD_DUAL_IMAGE_SLOT)'
    rpc = app / 'src/studio/rpc.c'
    selected = '    enum zmk_transport transport = zmk_endpoint_get_selected().transport;'
    replace(rpc, selected, '#if ' + only_host + '\n' + selected +
            '\n#else\n    enum zmk_transport transport = ZMK_TRANSPORT_USB;\n#endif', 'enum zmk_transport transport = ZMK_TRANSPORT_USB;')
    begin = '    struct zmk_endpoint_changed *ep_changed = as_zmk_endpoint_changed(eh);'
    end = '    struct zmk_studio_rpc_notification *rpc_notify ='
    replace(rpc, begin, '#if ' + only_host + ' /* PAD_HOST_LISTENER */\n' + begin, 'PAD_HOST_LISTENER')
    replace(rpc, end, '#endif /* PAD_HOST_LISTENER_END */\n' + end, 'PAD_HOST_LISTENER_END')
    sub = 'ZMK_SUBSCRIPTION(studio_rpc, zmk_endpoint_changed);'
    replace(rpc, sub, '#if ' + only_host + '\n' + sub + '\n#endif /* PAD_HOST_SUB */', 'PAD_HOST_SUB')
    hid = 'target_sources_ifdef(CONFIG_ZMK_USB app PRIVATE src/usb_hid.c)'
    replace(app / 'CMakeLists.txt', hid, 'if(NOT CONFIG_PAD_DUAL_IMAGE_SLOT)\n' + hid +
            '\nendif() # PAD_HOST_HID', 'PAD_HOST_HID')
if __name__ == '__main__': patch(sys.argv[1])
