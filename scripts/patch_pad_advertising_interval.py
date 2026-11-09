#!/usr/bin/env python3
"""Slow continuous Eyelash Pad advertising while disconnected."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
marker = "/* EYELASH_PAD_SLOW_ADVERTISING */"
if marker in source:
    sys.exit(0)

replacements = {
    "static int start_advertising(bool low_duty) {": """#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
/* EYELASH_PAD_SLOW_ADVERTISING */
static void pad_slow_advertising_interval(struct bt_le_adv_param *param) {
    /* Advertising interval units are 0.625 ms. */
    param->interval_min = 3200;
    param->interval_max = 4000;
}
#endif

static int start_advertising(bool low_duty) {""",
    "        return bt_le_adv_start(&adv_param, NULL, 0, NULL, 0);": """#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
        if (low_duty) {
            pad_slow_advertising_interval(&adv_param);
        }
#endif
        return bt_le_adv_start(&adv_param, NULL, 0, NULL, 0);""",
    "        return bt_le_adv_start(BT_LE_ADV_CONN_FAST_2, zmk_ble_ad, ARRAY_SIZE(zmk_ble_ad), NULL, 0);": """#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
        struct bt_le_adv_param adv_param = *BT_LE_ADV_CONN_FAST_2;
        pad_slow_advertising_interval(&adv_param);
        return bt_le_adv_start(&adv_param, zmk_ble_ad, ARRAY_SIZE(zmk_ble_ad), NULL, 0);
#else
        return bt_le_adv_start(BT_LE_ADV_CONN_FAST_2, zmk_ble_ad, ARRAY_SIZE(zmk_ble_ad), NULL, 0);
#endif""",
}

for old, new in replacements.items():
    if source.count(old) != 1:
        sys.exit(f"Unexpected ZMK peripheral source: {old}")
    source = source.replace(old, new)
path.write_text(source)
