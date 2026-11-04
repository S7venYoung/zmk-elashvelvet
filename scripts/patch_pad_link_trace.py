#!/usr/bin/env python3
"""Add diagnostic-only connection stages to the split central, fail on source drift."""
from pathlib import Path
import sys
MARKER = 'EYELASH_DIAGNOSTIC_LINK_TRACE'
def patch(text):
    if MARKER in text:
        return text
    needle = "    settings_register(&ble_central_settings_handler);"
    if text.count(needle) != 1:
        raise ValueError("Unexpected split settings registration")
    text = text.replace(needle, "    int diagnostic_register_rc = settings_register(&ble_central_settings_handler);")
    hooks = [
        ('    int diagnostic_register_rc = settings_register(&ble_central_settings_handler);', '    eyelash_diagnostic_stage(5, diagnostic_register_rc);'),
        ('    settings_loaded = true;', '    eyelash_diagnostic_stage(6, 0);'),
        ('    is_enabled = enabled;', '    eyelash_diagnostic_stage(7, enabled);'),
        ('    transport_status_cb = cb;', '    eyelash_diagnostic_stage(8, cb != 0);'),
        ('    int slot_idx = reserve_peripheral_slot(addr);', '    eyelash_diagnostic_stage(1, slot_idx);'),
        ('    // Stop scanning so we can connect to the peripheral device.\n    int err = stop_scanning();', '    eyelash_diagnostic_stage(2, err);'),
        ('    err = bt_conn_le_create(addr, BT_CONN_LE_CREATE_CONN, param, &slot->conn);', '    eyelash_diagnostic_stage(3, err);'),
        ('    int err = bt_le_scan_start(BT_LE_SCAN_PASSIVE, split_central_device_found);', '    eyelash_diagnostic_stage(4, err);'),
    ]
    for needle, inserted in hooks:
        if text.count(needle) != 1:
            raise ValueError(f'Expected one hook: {needle}')
        text = text.replace(needle, needle + '\n' + inserted)
    declaration = f'/* {MARKER}: built only for the receiver diagnostic variant. */\nextern void eyelash_diagnostic_stage(unsigned stage, int result);\n'
    text = declaration + text
    text += '\nint eyelash_diagnostic_scan_state(void) {\n    return (is_enabled ? 1 : 0) | (is_scanning ? 2 : 0) | (settings_loaded ? 4 : 0) | (transport_status_cb ? 8 : 0);\n}\n'
    return text
if __name__ == '__main__':
    path = Path(sys.argv[1]);path.write_text(patch(path.read_text()))
