#!/usr/bin/env python3
"""Give only Eyelash Pad RMK-style disconnected advertising sleep.

Connected idle uses ZMK's interrupt-driven matrix and CONFIG_ZMK_SLEEP=n.
The source guard deliberately rejects upstream drift instead of guessing.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
marker = '/* EYELASH_RMK_ADVERTISING_SLEEP */'
if marker in source:
    print('Pad RMK advertising sleep already installed')
    sys.exit(0)


def replace(old, new):
    global source
    assert source.count(old) == 1, f'Unexpected peripheral source: {old[:80]}'
    source = source.replace(old, new)

replace('static void advertising_cb(struct k_work *work) {', '''#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
/* EYELASH_RMK_ADVERTISING_SLEEP */
#include <zephyr/sys/atomic.h>
#include <zmk/events/position_state_changed.h>

static atomic_t pad_advertising_asleep;
static atomic_t pad_advertising_active;

static void pad_advertising_timeout_cb(struct k_work *work) {
    if (!enabled || is_connected) {
        return;
    }
    atomic_set(&pad_advertising_asleep, 1);
    int err = bt_le_adv_stop();
    if (err < 0 && err != -EALREADY) {
        // A transient stop failure must not leave the Pad unable to retry.
        atomic_clear(&pad_advertising_asleep);
    } else {
        atomic_clear(&pad_advertising_active);
    }
}

K_WORK_DELAYABLE_DEFINE(pad_advertising_timeout, pad_advertising_timeout_cb);
#endif

static void advertising_cb(struct k_work *work) {
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    if (!enabled || is_connected || atomic_get(&pad_advertising_asleep)) {
        return;
    }
#endif''')
replace('''        LOG_ERR("Failed to start advertising (%d)", err);
    }
}''', '''        LOG_ERR("Failed to start advertising (%d)", err);
    }
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    if (!err) {
        atomic_set(&pad_advertising_active, 1);
        // schedule (not reschedule): high-duty -> low-duty fallback must not
        // reset the five-minute budget for this disconnected session.
        k_work_schedule(&pad_advertising_timeout, K_SECONDS(300));
    }
#endif
}''')
replace('K_WORK_DEFINE(advertising_work, advertising_cb);', '''K_WORK_DEFINE(advertising_work, advertising_cb);

#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
static void pad_resume_advertising_cb(struct k_work *work) {
    if (enabled && !is_connected && !atomic_get(&pad_advertising_active)) {
        low_duty_advertising = false;
        atomic_clear(&pad_advertising_asleep);
        k_work_submit(&advertising_work);
    }
}

K_WORK_DEFINE(pad_resume_advertising, pad_resume_advertising_cb);

static int pad_key_wake_listener(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *event = as_zmk_position_state_changed(eh);
    // Recover even if the recycled callback did not run after a disconnect.
    if (event && event->state && enabled && !is_connected &&
        !atomic_get(&pad_advertising_active)) {
        k_work_submit(&pad_resume_advertising);
    }
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(eyelash_advertising_wake, pad_key_wake_listener);
ZMK_SUBSCRIPTION(eyelash_advertising_wake, zmk_position_state_changed);
#endif''')
replace('''    is_connected = (err == 0);
''', '''    is_connected = (err == 0);
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    if (is_connected) {
        k_work_cancel_delayable(&pad_advertising_timeout);
        atomic_clear(&pad_advertising_asleep);
        atomic_clear(&pad_advertising_active);
    }
#endif
''')
replace('''    enabled = en;
    if (en) {''', '''    enabled = en;
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    k_work_cancel_delayable(&pad_advertising_timeout);
    atomic_clear(&pad_advertising_asleep);
    atomic_clear(&pad_advertising_active);
#endif
    if (en) {''')
replace('''    is_connected = false;

    raise_zmk_split_peripheral_status_changed(''', '''    is_connected = false;
#if IS_ENABLED(CONFIG_SHIELD_EYELASH_NUMPAD)
    atomic_clear(&pad_advertising_active);
#endif

    raise_zmk_split_peripheral_status_changed(''')
path.write_text(source)
print('Installed Pad-only five-minute advertising sleep and key wake')
