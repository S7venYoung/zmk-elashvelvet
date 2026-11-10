> Current Pad recovery build: system-off is disabled and disconnected
> advertising stays available without a five-minute cutoff. The Pad keeps the
> initial fast directed attempt for a bonded receiver, then uses a 2–2.5 s
> interval for slow directed advertising. Unpaired advertising uses the same
> slow interval. Connected BLE and the GPIO interrupt driven matrix retain
> their existing idle behavior. After a disconnect, the Pad retries advertising
> after one second independently of the BLE connection recycle callback.
> While disconnected it refreshes the low duty advertiser every 30 seconds.
> Test by unplugging only the receiver for about two minutes, reconnecting it,
> and checking Pad key input without cycling Pad power.
> The policy below describes the earlier RMK-style experiment. Use
> `pad-local-dfu` for the current application-only OTA.

# Pad RMK-compatible idle policy

## Owning source

The original Pad repository at `b9fd173fc27dfdc002b157d8e7c9b585e822c70c`
uses RMK `936a2a828fddc195d20e42bd952119cd3afa8172` in both its original and
Codex builds. Both keyboard.toml files set
`split_central_sleep_timeout_seconds = 7200`. Despite its name, the pinned
`rmk/src/ble/sleep.rs` runs this manager for standalone BLE keyboards too.

Sources:
- https://github.com/S7venYoung/eyelash-codex-pad/blob/b9fd173fc27dfdc002b157d8e7c9b585e822c70c/firmware/original/keyboard.toml
- https://github.com/S7venYoung/eyelash-codex-pad/blob/b9fd173fc27dfdc002b157d8e7c9b585e822c70c/scripts/prepare-rmk.sh
- https://github.com/HaoboGu/rmk/blob/936a2a828fddc195d20e42bd952119cd3afa8172/rmk/src/ble/sleep.rs
- https://github.com/HaoboGu/rmk/blob/936a2a828fddc195d20e42bd952119cd3afa8172/rmk/src/ble/mod.rs
- https://github.com/HaoboGu/rmk/blob/936a2a828fddc195d20e42bd952119cd3afa8172/rmk/src/matrix.rs

RMK's two-hour sleep switches a software state and publishes a sleep event;
it does not power off or force a connected standalone keyboard to disconnect.
Activity clears it. An async matrix waits for GPIO activity when no keys need
rescanning. Unconnected advertising has a 300-second timeout, after which a
key/pointing event restarts advertising. HID host suspend can also request
software sleep. This Pad has no pointing sensor or display.

## ZMK behavior

The earlier ZMK Pad entered `sys_poweroff()` after 15 minutes. Merely extending
that to two hours still cold-boots and reconnects after long idle, unlike RMK.
The Pad now disables only system-off deep sleep (`CONFIG_ZMK_SLEEP=n`) and
uses a two-hour software idle default. ZMK's matrix remains interrupt-driven
and the CPU/BLE controller can idle normally. This is not disabling all power
saving. A live split connection is retained across long idle.

The Pad-only patch in `scripts/patch_pad_rmk_idle.py` stops unconnected
advertising after five minutes and resumes it on a physical key press. The
high-duty to low-duty directed advertising fallback does not renew that
budget. Connected links cancel the timeout. Work is submitted to the existing
system queue; no thread or receiver allocation is added. Stop errors permit
retry. A physical key also starts advertising after any disconnected state,
including when the controller omits Zephyr's `recycled` callback. Transport
disable still wins over key wake.

This preserves the observable connected-idle and disconnected-key-wake policy,
not binary-identical internals: RMK is standalone HID; this Pad is a ZMK split
peripheral. Host HID suspend is owned by the Dongle. RMK's battery notification
gating and split-central connection adaptation are not copied to this Pad.
ZMK retains its existing 60-second battery sampling and split connection
parameters (7.5 ms, latency 30, supervision 4 seconds); RMK's HID host link is
not equivalent. No claim of equal measured current or wake latency is made.

Velvet halves and receiver retain the 4512451 power configuration, including
15-second display idle and two-hour deep sleep (USB power blocks deep sleep).
The earlier 60-second display change is withdrawn: a screenless Pad's RMK
policy provides no evidence for changing the Velvet displays.

## Configuration, build and device checks

The fork persists runtime activity values under `activity/s`; existing values
are preserved. Pad cannot system-off even if old sleep settings exist because
the code path is compiled out. Its software idle default can still be replaced
by a stored idle value, which does not disconnect BLE or turn off the MCU.
No settings/bond clearing or migration is performed.

Host tests execute the actual patched advertising callbacks with Bluetooth
and work mocks: connected guard, 300-second budget, fallback, release/press
wake, disconnect without `recycled`, repeated keys, stop failure and disabled
transport. CI verifies the merged Pad `.config` and linked callback symbols,
plus unchanged DYA receiver stack/buffer/batched-notification fixes. Review
actual RAM in the new build.

Manual acceptance, without touching control Dongle .11101:
- Upgrade only the Pad via application OTA; stable .11201 needs no reflash.
- After 16 minutes and more than two hours idle with the receiver present,
  check immediate input, no cold boot and no missed first key.
- With the receiver unavailable, check advertising stops after five minutes;
  restore the receiver and press a Pad key to reconnect. That key initiates
  reconnect and is not guaranteed delivered while the link was absent.
- Repeat disconnect/wake cycles and test three peers plus DYA advanced settings.
- Measure current and battery life before claiming RMK-equivalent consumption.

No device is automatically flashed, reset, unplugged or power-cycled.
