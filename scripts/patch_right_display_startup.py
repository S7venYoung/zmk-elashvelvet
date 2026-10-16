#!/usr/bin/env python3
"""Restore right peripheral panel power after saved settings have loaded."""
from pathlib import Path
import sys

MARKER = "VELVET_RIGHT_DISPLAY_POWER_GUARD"
GUARD = """
#if IS_ENABLED(CONFIG_SHIELD_VELVET_RIGHT) && IS_ENABLED(CONFIG_SHIELD_VELVET_SPLIT_PERIPHERAL)
    /* VELVET_RIGHT_DISPLAY_POWER_GUARD: settings_load() precedes display init.
     * A saved EP_OFF must not leave this keyboard's status panel unpowered.
     * Scope is the right dongle peripheral, never the receiver or left half.
     */
    const struct device *panel_power = DEVICE_DT_GET(DT_INST(0, zmk_ext_power_generic));
    if (!device_is_ready(panel_power)) {
        LOG_ERR("Right display power device unavailable");
        return;
    }
    int power_state = ext_power_get(panel_power);
    if (power_state < 0) {
        LOG_ERR("Right display power state failed: %d", power_state);
        return;
    }
    if (!power_state) {
        int err = ext_power_enable(panel_power);
        if (err < 0) {
            LOG_ERR("Right display power restore failed: %d", err);
            return;
        }
        k_msleep(50);
        LOG_INF("Restored right display power after saved settings");
    }
#endif
"""


def patch(source):
    if MARKER in source:
        return source
    include = "#include <zephyr/drivers/display.h>"
    entry = "void initialize_display(struct k_work *work) {"
    if source.count(include) != 1 or source.count(entry) != 1:
        raise ValueError("Unexpected upstream display initializer")
    source = source.replace(include, include + "\n#include <drivers/ext_power.h>", 1)
    return source.replace(entry, entry + "\n" + GUARD, 1)


if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text()))
