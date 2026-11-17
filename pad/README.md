# Standalone nRF52840 Pad16

Experimental standalone USB/BLE configuration on the repository's nice_nano//zmk
board, using ZMK v0.4.0. Build manually with the
"Build standalone Pad16 nRF52840" Actions workflow on this branch.

Hardware interpretation:
- Rows 45, 47, 2, 29 use Nordic linear numbering: P1.13, P1.15, P0.02, P0.29.
- Columns 20, 22, 24, 32 become P0.20, P0.22, P0.24, P1.00.
- 16 WS2812-compatible RGB LEDs, assumed GRB order, data P0.11.
- powerpin 109 is provisionally interpreted as P1.09, active high.
- Matrix diodes are col2row, confirmed by the user.
- The nice!nano-compatible UF2 bootloader and 0x26000 application base
  must match the actual device before flashing.

Default numeric layout:
7 8 9 +
4 5 6 -
1 2 3 Enter
Fn 0 . Backspace

Hold bottom-left Fn for:
BLE profile 1 | BLE profile 2 | BLE profile 3 | Clear selected BLE pairing
USB output | BLE output | RGB on/off | Next RGB effect
Brighter | Dimmer | Restart | Bootloader
Fn | Num Lock | Divide | Multiply

Fn + row 3 column 4 enters the UF2 bootloader. This is a single-device
keyboard, so this combination is local and does not require a receiver.
The workflow produces pad52840_standalone.uf2 only.

Battery sensing and charging circuitry have not been identified, so battery
reporting is not configured. GPIO numbering, power-enable polarity, LED type,
and bootloader compatibility remain hardware assumptions to validate.
