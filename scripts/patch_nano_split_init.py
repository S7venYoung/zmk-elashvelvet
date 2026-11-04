#!/usr/bin/env python3
"""Ensure Nano split settings registration happens after bt_enable initializes settings.

With LTO, equal-priority SYS_INIT entries can place the split registration before
bt_enable(). The latter calls settings_subsys_init() on first startup and clears
the dynamic handler list, losing ble_central's commit callback. Give this board
an explicit ordering instead of relying on link order. No settings are erased.
"""
from pathlib import Path
import sys

MARKER = 'VELVET_NANO_ORDERED_SPLIT_INIT'
OLD = 'SYS_INIT(zmk_split_bt_central_init, APPLICATION, CONFIG_ZMK_BLE_INIT_PRIORITY);'
NEW = '''/* VELVET_NANO_ORDERED_SPLIT_INIT: bt_enable must initialize settings first. */
#if defined(CONFIG_SHIELD_VELVET_NANO_DONGLE)
SYS_INIT(zmk_split_bt_central_init, APPLICATION, UTIL_INC(CONFIG_ZMK_BLE_INIT_PRIORITY));
#else
SYS_INIT(zmk_split_bt_central_init, APPLICATION, CONFIG_ZMK_BLE_INIT_PRIORITY);
#endif'''

def patch(text):
    if MARKER in text:
        return text
    if text.count(OLD) != 1 or text.count('#include <zephyr/init.h>') != 1:
        raise ValueError('Unexpected split central initialization source')
    return text.replace('#include <zephyr/init.h>', '#include <zephyr/init.h>\n#include <zephyr/sys/util_macro.h>', 1).replace(OLD, NEW, 1)

if __name__ == '__main__':
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text()))
