#!/usr/bin/env python3
"""Keep Eyelash Pad advertising slowly and recover stalled reconnects."""
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
    "static void advertising_cb(struct k_work *work) {": """#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
static void pad_advertising_recovery_cb(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(pad_advertising_recovery, pad_advertising_recovery_cb);
#endif

static void advertising_cb(struct k_work *work) {
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    if (!enabled || is_connected) {
        return;
    }
#endif""",
    '        LOG_ERR("Failed to start advertising (%d)", err);\n    }\n}': """        LOG_ERR("Failed to start advertising (%d)", err);
    }
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    if (enabled && !is_connected) {
        /* Retry failures promptly; refresh a possibly stalled advertiser at low duty. */
        k_work_reschedule(&pad_advertising_recovery,
                          (err == 0 || err == -EALREADY) ? K_SECONDS(30) : K_SECONDS(1));
    }
#endif
}""",
    "K_WORK_DEFINE(advertising_work, advertising_cb);": """K_WORK_DEFINE(advertising_work, advertising_cb);

#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
static void pad_advertising_recovery_cb(struct k_work *work) {
    if (!enabled || is_connected) {
        return;
    }
    int err = bt_le_adv_stop();
    if (err && err != -EALREADY) {
        if (enabled && !is_connected) {
            k_work_reschedule(&pad_advertising_recovery, K_SECONDS(1));
        }
        return;
    }
    low_duty_advertising = true;
    advertising_cb(work);
}
#endif""",
    "    is_connected = (err == 0);": """    is_connected = (err == 0);
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    if (is_connected) {
        k_work_cancel_delayable(&pad_advertising_recovery);
    }
#endif""",
    """static void recycled(void) {
    if (enabled) {
        low_duty_advertising = false;
        k_work_submit(&advertising_work);
    }
}""": """static void recycled(void) {
    if (enabled) {
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
        /* Stopping the advertiser can itself recycle a connection object. */
        if (!is_connected) {
            k_work_schedule(&pad_advertising_recovery, K_SECONDS(30));
        }
#else
        low_duty_advertising = false;
        k_work_submit(&advertising_work);
#endif
    }
}""",
    "    is_connected = false;\n\n    raise_zmk_split_peripheral_status_changed(": """    is_connected = false;
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    if (enabled) {
        k_work_reschedule(&pad_advertising_recovery, K_SECONDS(1));
    }
#endif

    raise_zmk_split_peripheral_status_changed(""",
    "    enabled = en;\n    if (en) {": """    enabled = en;
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    if (!en) {
        k_work_cancel_delayable(&pad_advertising_recovery);
    } else {
        low_duty_advertising = false;
    }
#endif
    if (en) {""",
    "static bool is_connected = false;": """#include <errno.h>

static bool is_connected = false;""",

}

for old, new in replacements.items():
    if source.count(old) != 1:
        sys.exit(f"Unexpected ZMK peripheral source: {old}")
    source = source.replace(old, new)
path.write_text(source)
