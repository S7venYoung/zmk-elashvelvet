# Nano split state query

DYA's BLE-management `GetSplitInfo` response previously hard-coded
`peripheral_connected = false` for a split central. That value described the
adapter implementation, not the Nano receiver.

`scripts/patch_ble_management_split_info.py` now walks the live LE connection
pool when the request is handled. It counts only connections in the connected
state with the central role. The response sets `peripheral_connected` when at
least one such split connection exists. It also sets the nanopb `has_info`
presence flag; without that flag the nested response message is encoded as
empty even when all of its values were populated.

The check does not use the Prospector status-advertisement connection count or
the last advertised battery values. Those can lag behind a disconnect. A
future request from the receiver is therefore evidence for the connection
state at that moment; no bond, profile, or output-priority state is changed.
