# Nano Custom Settings RAM and stack profile

Custom Settings metadata uses callback encoding for the repeated constraints field, retaining the upstream constraint and option counts and protobuf field numbers. `scripts/patch_nano_settings_ram.py` checks the pinned source before applying the patch. It replaces the large inline arrays in the four metadata buffers with callbacks.

On 2026-11-04 the diagnostic receiver reported four fatal incidents in the low priority work thread. PC 0x36a24 in its exact ELF resolves to `z_check_stack_sentinel`; reason 2 indicates the sentinel was corrupted. DYA expanding Advanced Settings requests metadata through the list-settings worker on this queue. The constraint encoder alone has an approximately 896-byte stack frame, in addition to the notification and protobuf call chain. The fifth incident was a sysworkq freeze; its causal connection is not yet proven.

The Nano low priority stack is increased from 2048 to 4096 bytes. The normal `nano-stable` build excludes temporary Pad tracing, USB log CDC and log processing overhead, and retains ordered split initialization, three peripherals, DYA features and stored bonds. Diagnostic builds reduce the log buffer allocation to accommodate the larger work stack. Actual RAM use must be checked in the build output; build success does not prove runtime stack margin or reconnect behavior.

After flashing only the intended receiver, verify Pad input, repeatedly open Advanced Settings and check reconnect without clearing bonds. Keep the working second receiver unchanged as the control.
