#!/usr/bin/env python3
"""Keep Nano split scanning recoverable after controller failures.

ZMK's split central sets is_scanning before bt_le_scan_start(). A rejected
start can therefore leave the software flag true while the controller is not
scanning. Zephyr also returns -EALREADY when the host still owns an explicit
scan, so simply calling start again cannot detect a controller that silently
stopped.

This patch clears rejected starts, retries them every second, and periodically
stops and restarts an open split scan. The low-frequency restart reuses one
delayable work item on the system workqueue. It does not touch bonds or
settings.
"""
from pathlib import Path
import sys


MARKER = "VELVET_NANO_SPLIT_SCAN_RECOVERY"


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Unexpected split central source near: {old[:100]}")
    return source.replace(old, new, 1)


def patch(source):
    if MARKER in source:
        return source

    source = replace_once(
        source,
        "static bool is_scanning = false;\n",
        f"""static bool is_scanning = false;

/* {MARKER}: a boolean flag is not controller scan state. */
static void split_central_scan_retry_cb(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(split_central_scan_retry_work,
                               split_central_scan_retry_cb);
#define SPLIT_CENTRAL_SCAN_RETRY_DELAY K_SECONDS(1)
#define SPLIT_CENTRAL_SCAN_HEALTH_DELAY K_SECONDS(10)
#define SPLIT_CENTRAL_CONNECT_TIMEOUT K_SECONDS(15)
#define SPLIT_CENTRAL_CONNECT_ABORT_GRACE K_SECONDS(2)
""",
    )

    source = replace_once(
        source,
        """struct peripheral_slot {
    enum peripheral_slot_state state;
    struct bt_conn *conn;
""",
        """struct peripheral_slot {
    enum peripheral_slot_state state;
    struct bt_conn *conn;
    int64_t connecting_since;
    bool connection_abort_requested;
""",
    )

    source = replace_once(
        source,
        """    slot->state = PERIPHERAL_SLOT_STATE_OPEN;
""",
        """    slot->state = PERIPHERAL_SLOT_STATE_OPEN;
    slot->connecting_since = 0;
    slot->connection_abort_requested = false;
""",
    )

    source = replace_once(
        source,
        """            release_peripheral_slot(i);
            peripherals[i].state = PERIPHERAL_SLOT_STATE_CONNECTING;
            return i;
""",
        """            release_peripheral_slot(i);
            peripherals[i].state = PERIPHERAL_SLOT_STATE_CONNECTING;
            peripherals[i].connecting_since = k_uptime_get();
            return i;
""",
    )

    source = replace_once(
        source,
        """    peripherals[idx].state = PERIPHERAL_SLOT_STATE_CONNECTED;
    return 0;
""",
        """    peripherals[idx].state = PERIPHERAL_SLOT_STATE_CONNECTED;
    peripherals[idx].connecting_since = 0;
    peripherals[idx].connection_abort_requested = false;
    return 0;
""",
    )

    source = replace_once(
        source,
        """static int stop_scanning(void) {
    LOG_DBG("Stopping peripheral scanning");
    is_scanning = false;
""",
        """static int stop_scanning(void) {
    LOG_DBG("Stopping peripheral scanning");
    k_work_cancel_delayable(&split_central_scan_retry_work);
    is_scanning = false;
""",
    )

    source = replace_once(
        source,
        "static int start_scanning(void) {\n",
        """static void split_central_scan_retry_cb(struct k_work *work) {
    ARG_UNUSED(work);

    if (!is_enabled) {
        return;
    }

    bool has_unconnected = false;
    bool has_connecting = false;
    for (int i = 0; i < CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS; i++) {
        if (peripherals[i].state == PERIPHERAL_SLOT_STATE_CONNECTING) {
            int64_t elapsed = k_uptime_get() - peripherals[i].connecting_since;
            if (peripherals[i].connecting_since != 0 &&
                elapsed >= SPLIT_CENTRAL_CONNECT_TIMEOUT) {
                if (!peripherals[i].connection_abort_requested) {
                    peripherals[i].connection_abort_requested = true;
                    if (peripherals[i].conn == NULL) {
                        release_peripheral_slot(i);
                    } else {
                        int err = bt_conn_disconnect(peripherals[i].conn,
                                                     BT_HCI_ERR_REMOTE_USER_TERM_CONN);
                        if (err < 0) {
                            LOG_WRN("Split connection abort failed (err %d); releasing slot %d",
                                    err, i);
                            release_peripheral_slot(i);
                        }
                    }
                } else {
                    LOG_WRN("Split connection abort did not complete; releasing slot %d", i);
                    release_peripheral_slot(i);
                }
            }
        }

        if (peripherals[i].conn == NULL) {
            has_unconnected = true;
        }
        if (peripherals[i].state == PERIPHERAL_SLOT_STATE_CONNECTING) {
            has_connecting = true;
        }
    }

    if (!has_unconnected) {
        LOG_DBG("All split peripheral slots are connected");
        return;
    }

    if (has_connecting) {
        k_work_reschedule(&split_central_scan_retry_work,
                          SPLIT_CENTRAL_CONNECT_ABORT_GRACE);
        return;
    }

    if (is_scanning) {
        // Zephyr -EALREADY reflects its host flag, not whether the controller
        // is still scanning. A stop/start cycle refreshes that controller state.
        int stop_err = bt_le_scan_stop();
        if (stop_err < 0) {
            LOG_WRN("Split scan health stop failed (err %d)", stop_err);
        }
        is_scanning = false;
        LOG_DBG("Restarting split scan health guard");
    }

    int err = start_scanning();
    if (err < 0) {
        LOG_WRN("Split scan retry remains unavailable (err %d)", err);
    }
}

static int start_scanning(void) {
""",
    )

    source = replace_once(
        source,
        """    if (!is_enabled) {
        LOG_DBG("Not scanning, we're disabled");
        return 0;
    }

    // No action is necessary if central is already scanning.
    if (is_scanning) {
        LOG_DBG("Scanning already running");
        return 0;
    }
""",
        """    if (!is_enabled) {
        LOG_DBG("Not scanning, we're disabled");
        k_work_cancel_delayable(&split_central_scan_retry_work);
        return 0;
    }

    // No action is necessary if central is already scanning.
    if (is_scanning) {
        LOG_DBG("Scanning already running");
        k_work_reschedule(&split_central_scan_retry_work,
                          SPLIT_CENTRAL_SCAN_HEALTH_DELAY);
        return 0;
    }
""",
    )

    source = replace_once(
        source,
        """    if (!has_unconnected) {
        LOG_DBG("All devices are connected, scanning is unnecessary");
        return 0;
    }

    // Start scanning otherwise.
    is_scanning = true;
    int err = bt_le_scan_start(BT_LE_SCAN_PASSIVE, split_central_device_found);
    if (err < 0) {
        LOG_ERR("Scanning failed to start (err %d)", err);
        return err;
    }

    LOG_DBG("Scanning successfully started");
    return 0;
}
""",
        """    if (!has_unconnected) {
        LOG_DBG("All devices are connected, scanning is unnecessary");
        k_work_cancel_delayable(&split_central_scan_retry_work);
        return 0;
    }

    // Start scanning otherwise.
    is_scanning = true;
    int err = bt_le_scan_start(BT_LE_SCAN_PASSIVE, split_central_device_found);
    if (err < 0) {
        if (err == -EALREADY) {
            // The controller is already scanning even if our stale flag was not.
            k_work_reschedule(&split_central_scan_retry_work,
                              SPLIT_CENTRAL_SCAN_HEALTH_DELAY);
            LOG_DBG("Controller scan was already running");
            return 0;
        }

        // A failed start must never leave the software permanently "scanning".
        is_scanning = false;
        LOG_ERR("Scanning failed to start (err %d); retrying", err);
        k_work_reschedule(&split_central_scan_retry_work,
                          SPLIT_CENTRAL_SCAN_RETRY_DELAY);
        return err;
    }

    k_work_reschedule(&split_central_scan_retry_work,
                      SPLIT_CENTRAL_SCAN_HEALTH_DELAY);
    LOG_DBG("Scanning successfully started");
    return 0;
}
""",
    )

    return source


if __name__ == "__main__":
    path = Path(sys.argv[1])
    original = path.read_text()
    updated = patch(original)
    if updated != original:
        path.write_text(updated)
        print("Installed Nano split scan failure recovery")
    else:
        print("Nano split scan failure recovery already installed")
