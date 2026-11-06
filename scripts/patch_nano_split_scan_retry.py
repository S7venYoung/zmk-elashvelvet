#!/usr/bin/env python3
"""Recover Nano split scanning after a transient controller failure.

ZMK 0.2's split central sets is_scanning before bt_le_scan_start(). If start
fails and no another connection callback arrives, the flag remains true while
the controller is not scanning. This patch clears the false state and retries
on the existing system workqueue. It does not touch bonds or settings.
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
        k_work_cancel_delayable(&split_central_scan_retry_work);
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
            k_work_cancel_delayable(&split_central_scan_retry_work);
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

    k_work_cancel_delayable(&split_central_scan_retry_work);
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
