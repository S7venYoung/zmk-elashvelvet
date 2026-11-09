# Pad connection diagnosis

Target: `codex/nano-dongle-numpad`, nice_nano_k/nrf52833 + velvet_nano_dongle only.

The normal firmware defaults keep diagnostics off. A temporary build adds the official `zmk-usb-logging` snippet alongside Studio, creating a separate log CDC port. The normal three-peer build arguments, keymap and partitions are retained. `config/pad_dongle_diagnostic.conf` explicitly disables boot-time bond clearing and settings reset.

`PAD_LINK configured_slots=3 connected_mask=...` reports currently connected split slots, not an advertisement ACK. Slot numbering is zero-based. Per-slot records include HCI state and security level. Other logs are reduced to save flash. PAD_TRACE records the GATT requests needed to trace key delivery. No helper code calls pairing reset, writes settings, or changes advertising/scanning policy.

Preparation only: `python3 scripts/build_pad_diagnostic.py` prints the exact single-target command. It does not fetch, build, flash, clear bindings, or trigger Actions. In a prepared workspace, `--build` compiles the target after explicit build approval. The output must be named `velvet_nano_dongle_pad_diagnostic.uf2` to distinguish it from production firmware.

Capture after flashing: open the added log CDC port at 115200 before starting the idle test. Keep it recording from the working connection until the first failed key press. Preserve the failure state and bonds. Capture connection lines (`PAD_LINK`, `Connected`, `Disconnected`, `security`, `bond`, `discover`, `subscribe`, or connection errors), without retaining arbitrary typing logs or Bluetooth key material. Do not enable Bluetooth SMP key debug output. Restore the production Dongle UF2 after diagnosis.

Build verification: Actions run 41754254196 succeeded for revision a5319aa. FLASH uses 380704 bytes (93.88%); RAM uses 129840 bytes (99.06%). This is a temporary diagnostic image with only 1232 bytes of unallocated RAM. Physical connection diagnosis remains pending capture from this image.

After explicit approval, dispatch the existing registered `build.yml` workflow on `codex/nano-dongle-numpad` with `variant=pad-diagnostic`. Its normal firmware/bootloader/package jobs are skipped in diagnostic mode; only the single receiver is built. The default variant remains `normal`.


Expanded trace: PAD_TRACE stage 1 = split candidate slot reservation (>=0 success,
negative means rejected/no free slot); stage 2 = scan stop; stage 3 = connection
creation; stage 4 = scan start. Stages 2–4 report 0 on success or negative errno.
scan_flags bit 0 = transport enabled, bit 1 = scan flag in the split central
(the flag alone is not proof the controller is scanning; inspect stage 4 result).
Connection callbacks report HCI errors/reasons and security results. A connected
slot alone does not prove subscriptions or key delivery. Stages 12–15 record the primary service discovery request, service match,
characteristic discovery request and key notification subscription request.
A zero request result means the call was accepted. It does not prove delivery.
No pairing material is logged.


Initialization trace revision: scan_flags additionally includes bit 2 (settings
commit completed) and bit 3 (transport callback registered). PAD_INIT periodically
reports the reached stage bitmask and the most recent settings handler phase:
1=set entered, 2=set returned, 3=commit entered, 4=commit returned. Only subsystem
names are recorded; no setting values, bond keys or user typing are logged.
Stages 5=split settings registration result, 6=split commit reached, 7=transport
enabled argument, 8=status callback registered, 9=main settings initialization
entered, 10=settings subsystem initialization returned, 11=settings load returned.
The diagnostic instrumentation does not force-enable scanning or change ordering.


Nano init ordering fix: ELF a5319aa placed __init_zmk_split_bt_central_init
at 0x477ec before __init_zmk_ble_init at 0x477fc, both priority 50.
bt_enable's first settings_subsys_init clears settings_handlers, dropping the
previously registered ble_central dynamic commit handler. The Nano-only patch
moves split BLE initialization to UTIL_INC(CONFIG_ZMK_BLE_INIT_PRIORITY), so
Bluetooth/settings initialization precedes registration even with LTO. Verify
this order in the final ELF; physical reconnection remains a separate check.
