# 16Pad 硬件与独立模式配置

当前分支使用双镜像工作流。[刷机文件、模式切换、DYA 和灯效操作](dual/README.md)。以下记录独立模式的硬件配置与开发细节。

Current hardware pins (updated by the user on 2026-11-18):
- Rows `{24,13,29,30}`: P0.24, P0.13, P0.29, P0.30.
- Columns `{41,2,45,28}`: P1.09, P0.02, P1.13, P0.28.
- 16 WS2812-compatible RGB LEDs, assumed GRB order, data **P0.05**.
- Default diode-direction remains col2row; previous measurements used a
  superseded pin set and do not establish the direction of this new matrix.
- The old provisional powerpin 109/P1.09 conflicts with new column 0, and
  nice!nano's inherited EXT_POWER/P0.13 conflicts with new row 1. Both GPIO
  power-control instances are removed; matrix scanning owns these pins.
- The user subsequently confirmed POWER_PIN=GPIO(0,1). The replacement
  external-power control uses **P0.01**, provisionally active high (polarity
  has not been separately confirmed), with a 50-ms startup delay.
- Rasi S140 7.3.0 application start is 0x27000; keep RTC-fixed BL at 0xf4000.

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

Position-event capture on both the top and bottom physical rows produced no
events while the default layer remained active. The merged config enables
kscan and its GPIO matrix driver. The author-provided pin numbers are retained.
`pad/diagnostics` adds a read-only Studio custom subsystem `pad_matrix_diag`:
request protobuf `08 01` returns field 1 bytes (96-byte versioned snapshot).
It reports scanner device readiness, selected physical layout, layer mask,
GPIO0/1 IN/OUT/DIR and the eight matrix pins' PIN_CNF/current levels. It does
not configure GPIOs, pause scanning, write settings or inject keys. Native
Devtool log capture is also enabled to expose initialization errors.

The first GPIO snapshot reported ready scanner/layout 0, row inputs with
pull-down and high-level SENSE, all column output latches high, and P1.09
power control high. Holding the top-left physical key for 5 seconds caused
no observed changes. This establishes no signal with the current col2row
configuration; it does not prove which of wiring/pin numbering/direction
is responsible.

The manual application build has `reverse_matrix` (default false). Its
separate `pad/row2col-test.overlay` tests row2col with exactly the same row
and column GPIO lists, changing only their input/output/pull roles. The
artifact is named `pad52840-matrix-row2col-test`; it retains GPIO diagnostics
and is an experiment, not a verified fix. Standard builds retain col2row.

The row2col test produced input/events, but holding only the top-left key
activated positions 2, 6, 10, 14 simultaneously (9/6/3/dot). All released
on key-up. This proves signal activity in that direction but is not a
successful keymap fix. Both configured settling delays had been zero.
The opt-in test now waits 30 us before sampling and 50 us between outputs.
It additionally enables operation `08 02`: pause normal scanning, wait 5 ms
with all existing outputs inactive, then drive each existing output in turn
with 5-ms settle/discharge intervals, and restore scanning on exit. It never
changes GPIO modes or persistent settings. Operation 1 remains read-only.
Operation 2 is disabled in normal builds. Snapshot byte 76=2 marks a probe;
bytes 78..82 are idle and four driven input masks, and signed little-endian
words at 84/88 report probe/scan-resume errors. Hardware verification pending.

### Latest pin correction supersedes earlier experiments

The old `{45,47,2,29}` / `{20,22,24,32}` matrix and P0.11 RGB were replaced
by the current pin list above. Old GPIO captures and row2col/settling test
results must not be used to infer the new wiring. Diagnostic snapshots now
use version 2 (112 bytes), deriving the eight pins from DTS and carrying
(port,pin) pairs in bytes 96..111. Earlier field offsets are unchanged.
Do not flash earlier artifacts with the superseded pin set to validate this
configuration. No new build or hardware validation is claimed yet.

The final supplied hardware tuple is rows `{24,13,29,30}`, columns
`{41,2,45,28}`, RGB data P0.05 and POWER_PIN=GPIO(0,1). The Pad's only
external-power node now uses P0.01; the inherited P0.13 instance remains
deleted, and P1.09 remains exclusively a matrix column. Previous powerpin
109/P1.09 assumptions are superseded. No build or hardware validation yet.
