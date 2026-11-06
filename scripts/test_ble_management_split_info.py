#!/usr/bin/env python3
"""Apply and exercise the real DYA split connection counter."""
from pathlib import Path
import subprocess
import sys
import tempfile


def function(text, name):
    prefix = f"static void {name}(struct bt_conn *conn, void *data) {{"
    start = text.find(prefix)
    if start < 0:
        raise AssertionError(f"Missing patched function {name}")
    brace = text.index("{", start)
    depth = 0
    for pos in range(brace, len(text)):
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
            if depth == 0:
                return text[start:pos + 1]
    raise AssertionError(f"Unterminated function {name}")


upstream = Path(sys.argv[1])
patcher = Path(__file__).with_name("patch_ble_management_split_info.py")

with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    source = temp / "ble_management_handler.c"
    source.write_text(upstream.read_text())
    subprocess.run([sys.executable, str(patcher), str(source)], check=True)
    first = source.read_text()
    assert "VELVET_BLE_MANAGEMENT_SPLIT_CONNECTIONS" in first
    assert "#include <zephyr/bluetooth/conn.h>" in first
    assert "bt_conn_foreach(BT_CONN_TYPE_LE" in first
    assert "info->peripheral_connected = connections.central_connections > 0;" in first
    assert "result.has_info = true;" in first
    subprocess.run([sys.executable, str(patcher), str(source)], check=True)
    assert source.read_text() == first

callback = function(first, "count_split_central_connection")

harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define BT_CONN_ROLE_CENTRAL 1

enum bt_conn_state {
    BT_CONN_STATE_DISCONNECTED = 0,
    BT_CONN_STATE_CONNECTED = 1,
};

struct bt_conn { int unused; };
struct bt_conn_info {
    enum bt_conn_state state;
    uint8_t role;
};

struct split_connection_count {
    uint8_t central_connections;
};

static int info_result;
static enum bt_conn_state info_state;
static uint8_t info_role;

static int bt_conn_get_info(const struct bt_conn *conn, struct bt_conn_info *info) {
    (void)conn;
    info->state = info_state;
    info->role = info_role;
    return info_result;
}
'''

tests = r'''
int main(void) {
    struct bt_conn conn;
    struct split_connection_count count = {0};

    info_result = 0;
    info_state = BT_CONN_STATE_CONNECTED;
    info_role = BT_CONN_ROLE_CENTRAL;
    count_split_central_connection(&conn, &count);
    assert(count.central_connections == 1);

    info_role = 2;
    count_split_central_connection(&conn, &count);
    assert(count.central_connections == 1);

    info_role = BT_CONN_ROLE_CENTRAL;
    info_state = BT_CONN_STATE_DISCONNECTED;
    count_split_central_connection(&conn, &count);
    assert(count.central_connections == 1);

    info_state = BT_CONN_STATE_CONNECTED;
    info_result = -5;
    count_split_central_connection(&conn, &count);
    assert(count.central_connections == 1);
    return 0;
}
'''

with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    c_path = temp / "test.c"
    c_path.write_text(harness + callback + tests)
    executable = temp / "test"
    subprocess.run(
        ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(c_path), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)

print("DYA split info: connected central counted; peripheral, disconnected and error states ignored")
