# Nano split scan recovery

## Failure

The pinned ZMK split-central code sets `is_scanning = true` before calling
`bt_le_scan_start()`. A transient start failure leaves that software flag true
while the Bluetooth controller is not scanning. Later disconnect and connection
callbacks then take the "Scanning already running" branch forever. Restarting
the Nano Dongle is the only recovery in that build.

This was observed after a long idle period: the USB Dongle remained responsive,
but the Pad was not rediscovered and no further scanning occurred. The Pad
remained enumerated on USB, so the Pad MCU itself had not stopped. The other
configured peripheral slots were intentionally not treated as evidence because
only the Pad was connected for this diagnosis.

## Source change

`scripts/patch_nano_split_scan_retry.py` is applied only to the Nano Dongle
firmware builds. It:

- clears `is_scanning` whenever the controller rejects a real scan start;
- treats `-EALREADY` as a scan already owned by the Zephyr host;
- retries a rejected start every second on the existing system workqueue;
- stops and restarts an open scan every ten seconds, because Zephyr reports
  `-EALREADY` from its host flag even when repeated start calls cannot prove
  that the controller is still scanning;
- waits while a split connection attempt is making progress;
- aborts a split connection attempt after 15 seconds and force-releases the
  slot two seconds later if Zephyr never delivers the disconnect callback;
- cancels the guard after stop, disable, or full peer connectivity.

The change reuses one static delayable work item for both retry and health
checks. It adds no thread, queue, buffer, settings migration, bond clearing, or
forced re-pair operation.

The Pad's existing five-minute disconnected advertising stop and physical-key
wake remain in place. That policy is separate: the Pad may stop advertising
while idle, but a key press must restart it; the Dongle must keep its split
scanner recoverable.

## Automated verification

The host test applies the patcher twice to check idempotence, extracts the real
patched `start_scanning()`, `stop_scanning()`, and retry callback, and compiles
them with Bluetooth and workqueue mocks. It covers a failed start, repeated
retry failure, successful recovery, duplicate-start suppression, `-EALREADY`,
transport disable, full connectivity, and stop.
It also covers a stale `CONNECTING` slot that ignores its first abort request.

CI verifies the callback and work-item symbols in the linked ARM Dongle ELF and
reports the resulting RAM use. The normal Nano memory budget is only
2960 bytes free, so the build must retain the existing 4096-byte system
workqueue stack and configured split connection budget.

## Device acceptance

Use only the receiver/dongle firmware from a successful new build. Do not clear
settings or existing bonds. After flashing the Dongle, repeat the long-idle
scenario overnight and press one Pad key:

1. The Pad must resume advertising after its five-minute idle stop.
2. The Dongle must rediscover and reconnect without USB power cycling.
3. Normal typing and DYA advanced settings must continue to work.

Source and host tests do not prove the overnight hardware behavior. The
physical device must reproduce the sequence across more than one long idle
cycle before the fix is considered accepted.
