# Pad wake and idle policy

The Pad previously entered deep sleep after 900000 ms (15 minutes), versus
7200000 ms (two hours) for the Velvet halves. `app/src/activity.c` in the
cormoran ZMK fork enters `sys_poweroff()` on deep sleep after suspending devices.
A key wake consequently requires a boot and BLE reconnect/discovery, rather
than resuming an existing connected link. Extending the Pad timeout to two
hours avoids this path during typical intermittent numpad use while retaining
long-idle power saving. It does not accelerate boot or guarantee the wake key
is delivered after actual deep sleep.

Velvet idle/display blanking changes from 15 to 60 seconds. Idle is distinct
from deep sleep: the activity worker only raises the idle event; the split BLE
peripheral code does not subscribe to it or disconnect in response. USB power
prevents deep sleep on the receiver in this fork. The receiver shares the
Velvet idle default for its status advertisement cadence.

Split connections are created by `app/src/split/bluetooth/central.c` using
`ZMK_SPLIT_BLE_PREF_*`: interval 6 (7.5 ms), peripheral latency 30 and supervision
timeout 400 (4 seconds). `BT_PERIPHERAL_PREF_*` in `velvet.conf` describes the
receiver/keyboard's host-facing peripheral connection, not these split links.
Peripheral latency permits skipping connection events; it is not evidence of
a fixed 232.5 ms key delay. Preserve these parameters until device timing or
HCI disconnect evidence supports changing them. Reconnect already starts with
high-duty directed advertising for bonded peripherals and falls back to low
duty after its timeout. No scan/advertising patch is justified by the report
alone.

The fork persists runtime activity settings under `activity/s`. Those values
replace compiled defaults when present. Existing DYA idle/sleep customizations
are preserved, not silently reset. After updating the halves, inspect their
actual DYA idle/deep-sleep values and explicitly select 60000/7200000 ms if old
values remain. Pad has no settings RPC in this configuration; its default
changes on update unless an older firmware has stored an activity override.
Do not clear all settings or bonds to apply this policy.

CI checks the merged `.config` of all four application targets and retains
the DYA stack/buffer/batched-notification fixes. Confirm the new RAM report
before delivery. Compile checks cannot validate battery life or wake latency.

Device acceptance (manual, no automatic flashing):
- Leave .11101 unchanged. Do not unplug/reflash .11201 as part of investigation.
- With the new Pad application, test input after 30 s, 16 min and 60 min; the
  split connection should remain established (absent radio/power problems).
- With updated halves, check display blanking around 60 s and immediate input
  on wake from idle; verify runtime values first.
- After more than two hours idle on battery, verify wake/reconnect and check
  whether the first key is retained; record timing separately from idle wake.
- Reopen DYA advanced settings repeatedly and check watchdog records for
  regressions. Measure battery life over normal use before calling it stable.
