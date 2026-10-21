#!/usr/bin/env python3
"""Make the settings-reset application return to the bootloader on success."""
from pathlib import Path
import sys

ORIGINAL = "SYS_INIT(zmk_settings_erase, POST_KERNEL, CONFIG_ZMK_SETTINGS_RESET_ON_START_INIT_PRIORITY);"
REPLACEMENT = "#include <errno.h>\n#include <zephyr/kernel.h>\n#include <zephyr/logging/log.h>\n#include <zephyr/retention/bootmode.h>\n#include <zephyr/sys/reboot.h>\n\nLOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);\n\n/* Erase before application settings are loaded; only reboot on success. */\nstatic int reset_result;\nstatic int velvet_reset_settings(void) {\n    reset_result = zmk_settings_erase();\n    return reset_result;\n}\n\nstatic void velvet_reset_enter_bootloader(struct k_work *work) {\n    ARG_UNUSED(work);\n    int err = bootmode_set(BOOT_MODE_TYPE_BOOTLOADER);\n    if (err != 0) {\n        LOG_ERR(\"Settings erased, but bootloader request failed: %d\", err);\n        return;\n    }\n    sys_reboot(SYS_REBOOT_WARM);\n}\nK_WORK_DELAYABLE_DEFINE(velvet_reset_boot_work, velvet_reset_enter_bootloader);\n\nstatic int velvet_reset_finish(void) {\n    if (reset_result != 0) {\n        LOG_ERR(\"Settings erase failed; staying in reset firmware: %d\", reset_result);\n        return reset_result;\n    }\n    /* Let USB settle after the UF2 bootloader handed over to this app. */\n    return k_work_reschedule(&velvet_reset_boot_work, K_MSEC(1000)) < 0 ? -EIO : 0;\n}\n\nSYS_INIT(velvet_reset_settings, POST_KERNEL, CONFIG_ZMK_SETTINGS_RESET_ON_START_INIT_PRIORITY);\nSYS_INIT(velvet_reset_finish, APPLICATION, 99);\n"

def patch(path):
    path = Path(path)
    source = path.read_text()
    if REPLACEMENT in source:
        return
    if source.count(ORIGINAL) != 1:
        raise SystemExit(f"Unexpected settings reset implementation: {path}")
    path.write_text(source.replace(ORIGINAL, REPLACEMENT))

if __name__ == "__main__":
    patch(sys.argv[1])
