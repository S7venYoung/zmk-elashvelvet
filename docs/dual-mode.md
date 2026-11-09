# Velvet46 right-hand dual image

The test branch packages two right-hand ZMK applications and a selector into
one `velvet_right_dongle.uf2`. Flash the updated left UF2 once. It stays a
peripheral in both modes. The Nano application remains compatible with its
existing split peers.

| Mode | Left hand connects to | Right hand | Computer output |
| --- | --- | --- | --- |
| Nano (default) | Nano | Nano peripheral | Nano |
| Right host | Right hand | Split central | Right USB or BLE |

On the right keyboard, hold both ends of the top row (matrix row 0, columns 0
and 5) for two seconds, then release both keys. The two keys still perform
their normal bindings during the hold. The right keyboard saves the selection
and reboots. The left hand looks for the right-host beacon, connects with a
separate BLE identity, and falls back to the Nano after the right-host link
and beacon are gone. A right-host pairing is needed the first time. Test the
initial pairing with only one right-host Velvet keyboard nearby.

The right-host mode uses the normal ZMK nice!view status screen and HID.
The left hand uses the cat screen in this mode and retains its Nano theme
preference for when it returns. Nano mode retains the existing dashboard
and DYA connection through the receiver.

| Right-hand range | Use |
| --- | --- |
| `0x26000–0x26fff` | Selector, at the existing nice!nano app entry |
| `0x27000–0x81fff` | Nano-mode application |
| `0x82000–0xe6fff` | Right-host application |
| `0xe7000–0xeafff` | Right-host NVS settings and bonds |
| `0xeb000–0xebfff` | Persistent mode journal |
| `0xec000–0xf3fff` | Existing Nano-mode NVS settings and bonds |

The merged UF2 contains only the selector and application ranges. Actions
checks each image's vector table, addresses, family ID, and slot boundaries.
The Nano receiver still starts at `0x1000`. To return the right hand to a
single-image build, enter its normal UF2 bootloader and flash the original
right-hand firmware. The usual keyboard settings-reset UF2 targets the
original NVS partition only.
