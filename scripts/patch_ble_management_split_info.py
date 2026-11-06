#!/usr/bin/env python3
"""Report real central-role split connections through DYA GetSplitInfo.

The external BLE management module hard-coded peripheral_connected to false
for split centrals. Count established central-role LE connections at request
time so the receiver status is useful without changing bonds or settings.
"""
from pathlib import Path
import sys


MARKER = "VELVET_BLE_MANAGEMENT_SPLIT_CONNECTIONS"


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Unexpected BLE management source near: {old[:100]}")
    return source.replace(old, new, 1)


def patch(source):
    if MARKER in source:
        return source

    source = replace_once(
        source,
        '#include <zephyr/bluetooth/bluetooth.h>\n',
        f"""#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>

/* {MARKER}: get split topology from live connections, not status caches. */
""",
    )

    source = replace_once(
        source,
        """/**
 * Handle GetSplitInfoRequest
 */
static int handle_get_split_info_request(
""",
        """struct split_connection_count {
    uint8_t central_connections;
};

static void count_split_central_connection(struct bt_conn *conn, void *data) {
    struct bt_conn_info info;
    struct split_connection_count *count = data;

    if (bt_conn_get_info(conn, &info) == 0 &&
        info.state == BT_CONN_STATE_CONNECTED &&
        info.role == BT_CONN_ROLE_CENTRAL) {
        count->central_connections++;
    }
}

/**
 * Handle GetSplitInfoRequest
 */
static int handle_get_split_info_request(
""",
    )

    source = replace_once(
        source,
        """    info->is_central = true;
    // For central, check if peripheral is connected
    // Note: ZMK doesn't expose a direct API for this, so we'll set it to false
    // for now
    info->peripheral_connected = false;
    info->central_bonded       = false;
""",
        """    info->is_central = true;
    struct split_connection_count connections = {0};
    bt_conn_foreach(BT_CONN_TYPE_LE, count_split_central_connection, &connections);
    info->peripheral_connected = connections.central_connections > 0;
    info->central_bonded       = false;
""",
    )

    return source


if __name__ == "__main__":
    path = Path(sys.argv[1])
    original = path.read_text()
    updated = patch(original)
    if updated != original:
        path.write_text(updated)
        print("Installed DYA split connection reporting")
    else:
        print("DYA split connection reporting already installed")
