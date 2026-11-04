# Pad connection diagnosis (not built)

Target: `codex/nano-dongle-numpad`, nice_nano_k/nrf52833 + velvet_nano_dongle only.

The normal firmware defaults keep diagnostics off. A temporary build adds the official `zmk-usb-logging` snippet alongside Studio, creating a separate log CDC port. The normal three-peer build arguments, keymap and partitions are retained. `config/pad_dongle_diagnostic.conf` explicitly disables boot-time bond clearing and settings reset.

`PAD_LINK configured_slots=3 connected_mask=...` reports currently connected split slots, not an advertisement ACK. Slot numbering is zero-based. Per-slot records include HCI state and security level. Other logs are reduced to save flash, so discovery and subscription errors may not be visible. No helper code calls pairing reset, writes settings, or changes advertising/scanning policy.

Preparation only: `python3 scripts/build_pad_diagnostic.py` prints the exact single-target command. It does not fetch, build, flash, clear bindings, or trigger Actions. In a prepared workspace, `--build` compiles the target after explicit build approval. The output must be named `velvet_nano_dongle_pad_diagnostic.uf2` to distinguish it from production firmware.

Capture after flashing: use the added log CDC port at 115200, then power-cycle only Pad. Preserve bonds. Capture connection lines (`PAD_LINK`, `Connected`, `Disconnected`, `security`, `bond`, `discover`, `subscribe`, or connection errors), without retaining arbitrary typing logs or Bluetooth key material. Do not enable Bluetooth SMP key debug output. Restore the production Dongle UF2 after diagnosis.

Status: two Actions builds failed at the link stage; the second overflowed FLASH by 10136 bytes. This revision reduces other modules' logging further; it has not yet been built or tested on hardware.

After explicit approval, dispatch the existing registered `build.yml` workflow on `codex/nano-dongle-numpad` with `variant=pad-diagnostic`. Its normal firmware/bootloader/package jobs are skipped in diagnostic mode; only the single receiver is built. The default variant remains `normal`.


Expanded trace: PAD_TRACE stage 1 = split candidate slot reservation (>=0 success,
negative means rejected/no free slot); stage 2 = scan stop; stage 3 = connection
creation; stage 4 = scan start. Stages 2–4 report 0 on success or negative errno.
scan_flags bit 0 = transport enabled, bit 1 = scan flag in the split central
(the flag alone is not proof the controller is scanning; inspect stage 4 result).
Connection callbacks report HCI errors/reasons and security results. A connected
slot alone does not prove subscriptions or key delivery. No pairing material is logged.
