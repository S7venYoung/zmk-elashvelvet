"""Make Nano split subscriptions wait for security and retry failed CCC writes."""

from pathlib import Path
import sys


RETRY_MARKER = "VELVET_SPLIT_SUBSCRIPTION_RETRY"
SECURITY_GUARD = """    /* VELVET_SPLIT_SECURITY_GATE: encrypted CCCs must not be subscribed before
     * the link is secure. Existing bonds are reused; never erase them here. */
    if (bt_conn_get_security(conn) < BT_SECURITY_L2) {
        err = bt_conn_set_security(conn, BT_SECURITY_L2);
        if (err < 0 && err != -EALREADY) {
            LOG_ERR("Split link security request failed (%d)", err);
        }
        /* Do not block discovery of the other half while security is pending. */
        start_scanning();
        return;
    }

"""

RETRY_SUPPORT = r'''/* VELVET_SPLIT_SUBSCRIPTION_RETRY: Zephyr removes a subscription when its
 * encrypted CCC write fails, but ZMK historically kept the non-zero value
 * handle and treated that subscription as ready. Track the real completion
 * result and retry only the failed characteristic while the same link lives. */
enum split_central_subscription_kind {
    SPLIT_SUB_POSITION = BIT(0),
    SPLIT_SUB_SENSOR = BIT(1),
    SPLIT_SUB_RELAY_EVENT = BIT(2),
    SPLIT_SUB_BATTERY = BIT(3),
};

static int split_central_subscription_bit(struct peripheral_slot *slot,
                                          struct bt_gatt_subscribe_params *params) {
    if (params == &slot->subscribe_params) {
        return SPLIT_SUB_POSITION;
    }
#if ZMK_KEYMAP_HAS_SENSORS
    if (params == &slot->sensor_subscribe_params) {
        return SPLIT_SUB_SENSOR;
    }
#endif
#if IS_ENABLED(CONFIG_ZMK_SPLIT_RELAY_EVENT)
    if (params == &slot->relay_event_subscribe_params) {
        return SPLIT_SUB_RELAY_EVENT;
    }
#endif
#if IS_ENABLED(CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING)
    if (params == &slot->batt_lvl_subscribe_params) {
        return SPLIT_SUB_BATTERY;
    }
#endif
    return -EINVAL;
}

static uint16_t *split_central_saved_handle(struct peripheral_slot *slot,
                                            struct bt_gatt_subscribe_params *params) {
    if (params == &slot->subscribe_params) {
        return &slot->subscribe_retry_position_handle;
    }
#if ZMK_KEYMAP_HAS_SENSORS
    if (params == &slot->sensor_subscribe_params) {
        return &slot->subscribe_retry_sensor_handle;
    }
#endif
#if IS_ENABLED(CONFIG_ZMK_SPLIT_RELAY_EVENT)
    if (params == &slot->relay_event_subscribe_params) {
        return &slot->subscribe_retry_relay_event_handle;
    }
#endif
#if IS_ENABLED(CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING)
    if (params == &slot->batt_lvl_subscribe_params) {
        return &slot->subscribe_retry_battery_handle;
    }
#endif
    return NULL;
}

static void split_central_restore_saved_handle(struct peripheral_slot *slot,
                                               struct bt_gatt_subscribe_params *params) {
    uint16_t *saved = split_central_saved_handle(slot, params);
    if (params->value_handle == 0 && saved && *saved) {
        params->value_handle = *saved;
    }
}

static void split_central_cancel_subscribe_retry(struct peripheral_slot *slot) {
    atomic_set(&slot->subscribe_retry_mask, 0);
    (void)k_work_cancel(&slot->subscribe_retry_work);
}

static void split_central_schedule_subscribe_retry(
    struct peripheral_slot *slot, struct bt_gatt_subscribe_params *params) {
    int bit = split_central_subscription_bit(slot, params);
    if (bit < 0) {
        return;
    }

    atomic_or(&slot->subscribe_retry_mask, bit);
    (void)k_work_reschedule(&slot->subscribe_retry_work, K_MSEC(750));
}

static void split_central_subscribe_complete(struct bt_conn *conn, uint8_t err,
                                             struct bt_gatt_subscribe_params *params) {
    if (!conn) {
        return;
    }
    struct peripheral_slot *slot = peripheral_slot_for_conn(conn);
    if (!slot || slot->conn != conn) {
        return;
    }

    int bit = split_central_subscription_bit(slot, params);
    if (bit < 0) {
        return;
    }

    if (err == 0) {
        uint16_t *saved = split_central_saved_handle(slot, params);
        if (saved && params->value_handle) {
            *saved = params->value_handle;
        }
        atomic_and(&slot->subscribe_retry_mask, ~bit);
        LOG_DBG("[SUBSCRIPTION CONFIRMED] value_handle=0x%04x ccc_handle=0x%04x",
                params->value_handle, params->ccc_handle);
        return;
    }

    LOG_WRN("[SUBSCRIPTION FAILED] ATT err=%u value_handle=0x%04x ccc_handle=0x%04x",
            err, params->value_handle, params->ccc_handle);
    /* Zephyr removes the failed subscription and calls notify(NULL) first,
     * which clears value_handle in ZMK's notify callbacks. Restore the handle
     * discovered for this exact characteristic before scheduling the retry. */
    split_central_restore_saved_handle(slot, params);
    split_central_schedule_subscribe_retry(slot, params);
}

static void split_central_resume_subscribe_retries(struct peripheral_slot *slot) {
    if (slot && atomic_get(&slot->subscribe_retry_mask)) {
        (void)k_work_reschedule(&slot->subscribe_retry_work, K_NO_WAIT);
    }
}

static int split_central_subscribe(struct bt_conn *conn,
                                   struct bt_gatt_subscribe_params *params);

static void split_central_subscribe_retry_work(struct k_work *work) {
    struct peripheral_slot *slot =
        CONTAINER_OF(work, struct peripheral_slot, subscribe_retry_work);

    if (slot->state != PERIPHERAL_SLOT_STATE_CONNECTED || slot->conn == NULL ||
        bt_conn_get_security(slot->conn) < BT_SECURITY_L2) {
        return;
    }

    atomic_val_t failed = atomic_get(&slot->subscribe_retry_mask);
    if (!failed) {
        return;
    }

    struct {
        int bit;
        struct bt_gatt_subscribe_params *params;
    } subscriptions[] = {
        {SPLIT_SUB_POSITION, &slot->subscribe_params},
#if ZMK_KEYMAP_HAS_SENSORS
        {SPLIT_SUB_SENSOR, &slot->sensor_subscribe_params},
#endif
#if IS_ENABLED(CONFIG_ZMK_SPLIT_RELAY_EVENT)
        {SPLIT_SUB_RELAY_EVENT, &slot->relay_event_subscribe_params},
#endif
#if IS_ENABLED(CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING)
        {SPLIT_SUB_BATTERY, &slot->batt_lvl_subscribe_params},
#endif
    };

    for (size_t i = 0; i < ARRAY_SIZE(subscriptions); i++) {
        struct bt_gatt_subscribe_params *params = subscriptions[i].params;
        split_central_restore_saved_handle(slot, params);
        if ((failed & subscriptions[i].bit) && params->value_handle) {
            LOG_DBG("[RETRY SUBSCRIPTION] value_handle=0x%04x ccc_handle=0x%04x",
                    params->value_handle, params->ccc_handle);
            (void)split_central_subscribe(slot->conn, params);
        }
    }
}

static int split_central_subscribe(struct bt_conn *conn,
                                   struct bt_gatt_subscribe_params *params) {
    struct peripheral_slot *slot = peripheral_slot_for_conn(conn);
    uint16_t *saved = slot ? split_central_saved_handle(slot, params) : NULL;
    if (saved && params->value_handle) {
        *saved = params->value_handle;
    }
    atomic_set(params->flags, BT_GATT_SUBSCRIBE_FLAG_NO_RESUB);
    params->subscribe = split_central_subscribe_complete;
    int err = bt_gatt_subscribe(conn, params);
    switch (err) {
    case -EALREADY: {
        struct peripheral_slot *slot = peripheral_slot_for_conn(conn);
        int bit = slot ? split_central_subscription_bit(slot, params) : -EINVAL;
        if (bit >= 0) {
            atomic_and(&slot->subscribe_retry_mask, ~bit);
        }
        LOG_DBG("[ALREADY SUBSCRIBED]");
        break;
    }
    case 0:
        LOG_DBG("[SUBSCRIBE SENT]");
        break;
    default: {
        struct peripheral_slot *slot = peripheral_slot_for_conn(conn);
        LOG_ERR("Subscribe failed (err %d)", err);
        if (slot) {
            split_central_schedule_subscribe_retry(slot, params);
        }
        break;
    }
    }

    return err;
}
'''


def _replace_once(source, old, new, description):
    if source.count(old) != 1:
        raise ValueError(f"Unexpected {description}: expected one anchor, found {source.count(old)}")
    return source.replace(old, new, 1)


def patch(source):
    if RETRY_MARKER in source:
        return source

    source = _replace_once(
        source,
        "static int start_scanning(void);\n",
        """static int start_scanning(void);
struct peripheral_slot;
static void split_central_cancel_subscribe_retry(struct peripheral_slot *slot);
static void split_central_subscribe_retry_work(struct k_work *work);
""",
        "start-scanning declaration",
    )

    source = _replace_once(
        source,
        """struct peripheral_slot {
    enum peripheral_slot_state state;
    struct bt_conn *conn;
""",
        """struct peripheral_slot {
    enum peripheral_slot_state state;
    struct bt_conn *conn;
    struct k_work subscribe_retry_work;
    atomic_t subscribe_retry_mask;
    uint16_t subscribe_retry_position_handle;
    uint16_t subscribe_retry_sensor_handle;
    uint16_t subscribe_retry_relay_event_handle;
    uint16_t subscribe_retry_battery_handle;
""",
        "peripheral slot retry fields",
    )

    source = _replace_once(
        source,
        """    LOG_DBG("Releasing peripheral slot at %d", index);

    if (slot->conn != NULL) {
""",
        """    LOG_DBG("Releasing peripheral slot at %d", index);

    split_central_cancel_subscribe_retry(slot);

    if (slot->conn != NULL) {
""",
        "slot release cleanup",
    )

    source = _replace_once(
        source,
        """            // Be sure the slot is fully reinitialized.
            release_peripheral_slot(i);
            peripherals[i].state = PERIPHERAL_SLOT_STATE_CONNECTING;
""",
        """            // Be sure the slot is fully reinitialized.
            release_peripheral_slot(i);
            k_work_init(&peripherals[i].subscribe_retry_work,
                        split_central_subscribe_retry_work);
            atomic_set(&peripherals[i].subscribe_retry_mask, 0);
            peripherals[i].state = PERIPHERAL_SLOT_STATE_CONNECTING;
""",
        "slot retry initialization",
    )

    begin = source.index("static int split_central_subscribe(struct bt_conn *conn, ")
    end_marker = "\nstatic int update_peripheral_selected_layout("
    end = source.index(end_marker, begin)
    source = source[:begin] + RETRY_SUPPORT + source[end:]

    begin = source.index("static void split_central_process_connection(struct bt_conn *conn) {")
    end = source.index("static int stop_scanning", begin)
    part = source[begin:end]
    anchor = "    if (!slot->subscribe_params.value_handle) {"
    part = _replace_once(part, anchor, SECURITY_GUARD + anchor, "split discovery security gate")
    source = source[:begin] + part + source[end:]

    begin = source.index("static void split_central_security_changed(")
    end = source.index("static struct bt_conn_cb conn_callbacks", begin)
    part = source[begin:end]
    part = _replace_once(
        part,
        "if (!slot || !slot->selected_physical_layout_handle) {",
        "if (!slot) {",
        "split security callback guard",
    )
    part = _replace_once(
        part,
        "    k_work_submit(&update_peripherals_selected_layouts_work);",
        """    /* A successful security event also resumes first-time discovery and any
     * CCC retry that was waiting for encryption. Existing subscriptions stay intact. */
    split_central_process_connection(conn);
    split_central_resume_subscribe_retries(slot);
    if (slot->selected_physical_layout_handle) {
        k_work_submit(&update_peripherals_selected_layouts_work);
    }""",
        "split security callback completion",
    )
    source = source[:begin] + part + source[end:]
    return source


if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text()))
