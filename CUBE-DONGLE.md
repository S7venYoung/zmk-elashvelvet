# ESP32-S3 Xingzhi Cube dongle — experimental peripherals

Base: `codex/zmk04-dya-Prospector-dongle` at `61d1e5d63e6f176058f4869a1c3ab2a8608ee746`. Original branch untouched.

This branch builds `velvet_left_cube.uf2`, `velvet_right_cube.uf2` and `settings_reset.uf2`. Both halves explicitly use `CONFIG_ZMK_SPLIT_ROLE_CENTRAL=n`; wiring, physical layout and keymap are unchanged. It targets the existing nice_nano boards and nice_view/nice_view_custom displays, not the Cube itself. The right half no longer acts as a computer-connected central. Reduced slave latency requests prioritize testing input latency; actual timing is negotiated by the central, and battery impact needs measurement.

ZMK `cormoran/main+dya` is pinned to `e5c9b6915b56801193e359dd9bad4a167ce0d1b8` for stable split GATT protocol development. Other module revisions remain inherited; this is not a fully reproducible dependency lock. Existing DYA relay configuration stays present; its event/RPC handling is not yet implemented by the Cube prototype.

The Cube development branch is `S7venYoung/ESP32-S3-Cube-Scanner:codex/xingzhi-cube-dongle`. Its experimental core is not integrated with BLE or USB and is not ready for normal keyboard use. **Do not replace your working keyboard firmware yet**: without a working Cube central these peripherals cannot type into the computer. A successful Action build only verifies compilation, not pairing or HID behavior.

Before hardware tests, save the working firmware and record Bluetooth bonds. Switching central requires an explicit reset/re-pair procedure; do not clear settings automatically. The existing keymap includes layers, media keys, Bluetooth management and a cross-half bootloader combo. The Cube must reproduce those behaviors, not simply map every position to a base-layer USB key. Until then only a limited bench test is valid.

Position GATT source: https://github.com/cormoran/zmk/blob/e5c9b6915b56801193e359dd9bad4a167ce0d1b8/app/src/split/bluetooth/service.c
