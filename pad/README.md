# Standalone nRF52840 Pad16

Experimental standalone USB/BLE configuration on the repository's nice_nano//zmk
board, using the repository’s ZMK 0.4 / Zephyr 4.1 DYA fork. Build manually with the
"Build standalone Pad16 nRF52840" Actions workflow on this branch.

Hardware interpretation:
- Rows 45, 47, 2, 29 use Nordic linear numbering: P1.13, P1.15, P0.02, P0.29.
- Columns 20, 22, 24, 32 become P0.20, P0.22, P0.24, P1.00.
- 16 WS2812-compatible RGB LEDs, assumed GRB order, data P0.11.
- powerpin 109 is provisionally interpreted as P1.09, active high.
- Matrix diodes are col2row, confirmed by the user.
- The nice!nano-compatible UF2 bootloader and 0x27000 application base
  matches the S140 size read from this device at 0x3008.

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

DYA connects over the USB CDC Studio channel. Devtool → Bootloader uses the
native devtool RPC. Studio is unlocked by default on this standalone Pad.

The UF2 completion optimization from commit 1ffe99d is a bootloader change.
Its patch and tests are retained under bootloader-test in this branch. It is
not incorporated into the application UF2. The Pad-specific bootloader adaptation below preserves the identified Rasi
USB IDs, recovery pins, flash partitions and board identity. The Nano33 BL
HEX must never be flashed to this nRF52840 Pad.

## Rasi BL short-power-cycle recovery

The installed INFO_UF2 identifies `Rasi_NRF_840BL`, S140 7.3.0 and commit
`b1d9a09`. The matching public source is
https://github.com/kbladewht/Adafruit_nRF52_Bootloader/tree/b1d9a09665e9766b6fcd656e9788562c2cc72bac/src/boards/feather_nrf52840_rasi
Its board.mk selects nRF52840; the nRF52833 Board-ID string is inherited from
that source. The installed `dirty` suffix means uncommitted vendor changes
cannot be identified from INFO_UF2 alone.

`bootloader-test/prepare_pad.py` reuses the Nano journal and power-cycle logic,
USB timeout fix and 1-second UF2 completion grace period. It keeps the Rasi
USB identifiers, board GPIOs, S140 version and 0xf4000 BL start. The journal
is moved to 0xea000–0xeafff; the Pad application starts at 0x27000 and ends before 0xea000 and NVS
remains at 0xec000. This is separate from Nano's 0x65000 journal.

Turn battery power **off** first. Plug in USB and unplug within 1 second,
repeat once, then plug in and leave connected. The third cold power-on enters
BL without running the application. Each short power-on must be under the
2-second counting window. A normal power-on waits about 2 seconds and clears
the count. With the battery still supplying the MCU, USB unplugging does not
count. Existing double-reset, key binding and DYA Bootloader paths remain.

The manual Pad workflow has a `bootloader` checkbox, default off. When checked,
it builds only the Pad BL and exports `pad52840_BL_ONLY.hex` (SWD, no mass erase)
and `pad52840_BL_UPDATE.uf2` (bootloader self-update). Keep the installed S140;
neither file is a replacement application. Do not use Nano33 BL images here.
Source patch/USB host tests and the Pad BL/reset Actions build passed in
run 44039479519 (commit a7f62c4). Downloaded UF2 address/family checks passed.
Pad BL and reset behavior still require hardware validation; no device was flashed.

The BL build also exports `settings_reset_pad.uf2`. It erases the Pad settings
and Bluetooth bonds, then requests BL after a 1-second USB settling delay.
After reset, flash `pad52840_standalone.uf2` again. Reset is for first-install
pairing cleanup or recovery, not required for routine firmware updates.
The BL self-update UF2 contains 0xf4000–0xfdfff BL flash plus one required
UICR verification block (bootloader=0xf4000, MBR params=0xfe000), with family
0xd663823c. The old BL validates this metadata without writing UICR. MBR and
application payloads are excluded. The initial flash-only UF2 from run
44039479519 was rejected by the old BL because this metadata was missing;
use the corrected 161-block updater instead.

Readback on 2026-11-17 confirmed application bytes were written correctly,
but S140 at 0x3008 reports application start 0x27000. Earlier Pad application
and reset artifacts linked at 0x26000 are incompatible with this device and
must not be reused. They overwrite the last S140 page (0x26000–0x26fff).
Restore that page from the matching original S140 7.3.0 before loading the
corrected 0x27000 application/reset. Keep the Rasi BL at 0xf4000.

A fresh BL session read back all 234,752 application bytes correctly but never
rebooted. The SDK stops RTC1 when no timers are active; zero-timeout DFU thus
cannot advance the UF2 quiet-window clock. `patch_pad_clock.py` keeps a 100-ms
repeating SDK timer running during USB DFU, without performing flash writes
inside timer callbacks. This fix is Pad-only pending a separate Nano review.

After the RTC-fixed BL was installed, reset and S140 both read back exactly,
and UF2 transfers exited BL, but neither ZMK image enumerated over USB. Rasi
BL explicitly uses internal RC LFCLK; Zephyr defaults to external LFXO.
The Pad app/reset now select calibrated internal RC with 500-ppm BLE timing.
This removes the external low-frequency crystal dependency; absence of that
crystal on the actual Pad and resolution of the startup issue are still
unverified. Builds export the merged config and DTS for inspection.

The RC reset still did not return to BL. Merged DTS showed nice!nano REG1
mode DCDC and REG0 enabled. Zephyr nrf52 soc.c enables both converters at
PRE_KERNEL_1 priority 0 from these DT values, even with CONFIG_REGULATOR off.
Rasi BL defaults ENABLE_DCDC_0 and ENABLE_DCDC_1 to 0. Both Pad overlays now
select REG1 LDO and disable REG0, matching that working BL configuration.
This removes a real board-default mismatch; hardware cause/resolution remain
to be verified. The app and reset must both use these overrides.

## Matrix verification

USB currently enumerates as Pad16. Read-only Studio RPC confirmed both stored
layers exactly match pad52840.keymap. Physical row/column orientation is not
yet verified. Enable Devtool layer-state and event-tap diagnostics to inspect
active layers and position transitions; no key injection is enabled. During
matrix tests subscribe only to position/layer events, then unsubscribe after
the test. Do not reset stored keymaps or change pin order based only on typed
characters: Fn actions can be non-printing and may change the host output.
