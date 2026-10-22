# Nano Custom Settings RAM profile

Actions 39739620890 linked the nRF52833 receiver over its 128 KiB RAM limit by 14,648 bytes; both keyboard halves built successfully. The map shows four Custom Settings metadata buffers of approximately 7 KiB each. This comes from the upstream nanopb constraint array (8 constraints, each containing an 8-value option union), not Tap Dance recursion or display RAM.

The Nano build applies scripts/patch_nano_settings_ram.py after west update and before CMake/protobuf generation. It bounds SettingMeta to two constraints per setting while retaining eight option values/labels per option constraint. Wire tags and setting values remain unchanged. Excess constraint metadata returns ENOMEM instead of silently truncating. Future settings needing more than two constraints require revisiting this profile.

This targets the dominant static allocation instead of cutting Bluetooth buffers, behavior queues or known-safe boot/RPC stack sizes. The expected saving across the four map buffers is approximately 20 KiB; actual final RAM usage must be confirmed by the next Actions link. The patch checks pinned-source anchors, is idempotent and fails on unexpected upstream layout changes. No automatic build is enabled.
