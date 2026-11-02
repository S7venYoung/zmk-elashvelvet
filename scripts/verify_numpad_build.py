#!/usr/bin/env python3
"""Check actual compiled roles and layouts, not just the source manifest."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "build")
central = root / "velvet_nano_dongle/zephyr/.config"
peripheral = root / "eyelash_numpad_peripheral/zephyr/.config"
for path in (central, peripheral):
    assert path.exists(), f"Missing compiled target: {path}"

text = central.read_text()
for line in ("CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS=3", "CONFIG_BT_MAX_CONN=4",
             "CONFIG_BT_MAX_PAIRED=8", "CONFIG_ZMK_STUDIO=y"):
    assert line in text, (central, line)

text = peripheral.read_text()
for line in ("CONFIG_ZMK_SPLIT=y", "# CONFIG_ZMK_SPLIT_ROLE_CENTRAL is not set",
             "# CONFIG_ZMK_STUDIO is not set", "# CONFIG_ZMK_RUNTIME_MACRO is not set",
             "# CONFIG_ZMK_RUNTIME_TAPDANCE is not set", "# CONFIG_ZMK_RUNTIME_COMBO is not set",
             "CONFIG_BT_MAX_CONN=1", "CONFIG_ZMK_BEHAVIOR_EYELASH_DFU=y"):
    assert line in text, (peripheral, line)

for target in ("velvet_nano_dongle", "velvet_left_dongle", "velvet_right_dongle",
               "eyelash_numpad_peripheral"):
    zephyr = root / target / "zephyr"
    header = next(zephyr.rglob("devicetree_generated.h"))
    text = header.read_text()
    lengths = [int(value) for value in re.findall(
        r"#define DT_N_S_keymap_S_\S+_P_bindings_LEN\s+(\d+)", text)]
    assert lengths and all(length == 77 for length in lengths), (target, lengths)
    assert list((root / target).rglob("behavior_eyelash_dfu.c.obj")), target

assert (root / "eyelash_numpad_peripheral/zephyr/zmk.hex").is_file()
print("Verified: three peers, stable 77-key layout, DYA on dongle, lightweight numpad, local DFU")
