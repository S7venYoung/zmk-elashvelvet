"""Apply the Velvet dual-mode hooks to the matching ZMK source checkout."""

from pathlib import Path
import shutil
import sys


def replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one ZMK hook anchor: {old!r}")
    return source.replace(old, new, 1)


def patch(path, transform):
    source = path.read_text()
    if "VELVET_DUAL_MODE_HOOK" not in source:
        path.write_text("/* VELVET_DUAL_MODE_HOOK */\n" + transform(source))


def startup(source):
    return replace(source, "    settings_load();\n#endif", """#if IS_ENABLED(CONFIG_SHIELD_VELVET_HOST_DIAGNOSTIC)
    LOG_INF("RIGHT HOST: main reached, loading settings");
#endif
    settings_load();
#if IS_ENABLED(CONFIG_SHIELD_VELVET_HOST_DIAGNOSTIC)
    LOG_INF("RIGHT HOST: settings loaded");
#endif
#endif

#if IS_ENABLED(CONFIG_VELVET_DUAL_LEFT) || IS_ENABLED(CONFIG_SHIELD_VELVET_DUAL_HOST)
    extern void velvet_dual_link_start(void);
    velvet_dual_link_start();
#if IS_ENABLED(CONFIG_SHIELD_VELVET_HOST_DIAGNOSTIC)
    LOG_INF("RIGHT HOST: link startup returned; entering display initialization");
#endif
#endif""")


def local_matrix(source):
    anchor = "        bool pressed = (ev.state == ZMK_KSCAN_EVENT_STATE_PRESSED);"
    return replace(source, anchor, anchor + """
#if IS_ENABLED(CONFIG_VELVET_DUAL_RIGHT)
        extern void velvet_dual_right_matrix(uint32_t row, uint32_t column, bool pressed);
        velvet_dual_right_matrix(ev.row, ev.column, pressed);
#endif""")


def peripheral(source):
    source = replace(source, 'static bool is_connected = false;', """
#if IS_ENABLED(CONFIG_VELVET_DUAL_LEFT)
#include "velvet_dual_link.h"
#include <zephyr/sys/atomic.h>

static atomic_t selected_identity;
static const struct bt_data right_host_ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, VELVET_LEFT_HOST_UUID),
};
#endif

static bool is_connected = false;""")
    source = replace(source, "    bt_foreach_bond(BT_ID_DEFAULT, each_bond, &central_addr);", """
    uint8_t identity = BT_ID_DEFAULT;
#if IS_ENABLED(CONFIG_VELVET_DUAL_LEFT)
    identity = (uint8_t)atomic_get(&selected_identity);
#endif
    bt_foreach_bond(identity, each_bond, &central_addr);""")
    source = replace(source, "        return bt_le_adv_start(&adv_param, NULL, 0, NULL, 0);",
                     "        adv_param.id = identity;\n"
                     "        return bt_le_adv_start(&adv_param, NULL, 0, NULL, 0);")
    source = replace(source, "        is_bonded = false;\n        return bt_le_adv_start", """
        is_bonded = false;
#if IS_ENABLED(CONFIG_VELVET_DUAL_LEFT)
        if (identity != BT_ID_DEFAULT) {
            struct bt_le_adv_param param = *BT_LE_ADV_CONN_FAST_2;
            param.id = identity;
            return bt_le_adv_start(&param, right_host_ad, ARRAY_SIZE(right_host_ad), NULL, 0);
        }
#endif
        return bt_le_adv_start""")
    anchor = "static void notify_transport_status(void);"
    return replace(source, anchor, """
#if IS_ENABLED(CONFIG_VELVET_DUAL_LEFT)
static void disconnect_old_host(struct bt_conn *conn, void *data) {
    int *result = data;
    *result = bt_conn_disconnect(conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
}

void velvet_dual_left_select_identity(uint8_t identity) {
    atomic_set(&selected_identity, identity);
    k_work_cancel(&advertising_work);
    bt_le_adv_stop();

    int err = -ENOTCONN;
    bt_conn_foreach(BT_CONN_TYPE_LE, disconnect_old_host, &err);
    /* The recycled callback starts directed advertising after a disconnect. */
    if (err == -ENOTCONN && enabled) {
        low_duty_advertising = false;
        k_work_submit(&advertising_work);
    } else if (err) {
        LOG_ERR("Cannot disconnect the old Velvet split host (%d)", err);
    }
}
#endif

""" + anchor)


def central(source):
    anchor = "static bool split_central_eir_parse"
    source = replace(source, anchor, """
#if IS_ENABLED(CONFIG_SHIELD_VELVET_DUAL_HOST)
#include "velvet_dual_link.h"
#define VELVET_DISCOVERY_UUID VELVET_LEFT_HOST_UUID
#else
#define VELVET_DISCOVERY_UUID ZMK_SPLIT_BT_SERVICE_UUID
#endif

""" + anchor)
    start = source.index(anchor)
    end = source.index("static void split_central_device_found", start)
    return (source[:start] +
            source[start:end].replace("ZMK_SPLIT_BT_SERVICE_UUID", "VELVET_DISCOVERY_UUID") +
            source[end:])


def nice_view_fonts(source):
    return replace(source, "    select LV_FONT_MONTSERRAT_26\n",
                   "    select LV_FONT_MONTSERRAT_26 if !SHIELD_VELVET_DUAL_HOST\n")


if __name__ == "__main__":
    app = Path(sys.argv[1])
    ble = app / "src/split/bluetooth"
    shutil.copyfile(Path(__file__).resolve().parents[1] / "dual-mode/link.h",
                    ble / "velvet_dual_link.h")
    patch(app / "src/main.c", startup)
    patch(app / "src/physical_layouts.c", local_matrix)
    patch(ble / "peripheral.c", peripheral)
    patch(ble / "central.c", central)
    fonts = app / "boards/shields/nice_view/Kconfig.defconfig"
    # Kconfig uses hash comments rather than the C hook marker.
    source = fonts.read_text()
    if "if !SHIELD_VELVET_DUAL_HOST" not in source:
        fonts.write_text(nice_view_fonts(source))
