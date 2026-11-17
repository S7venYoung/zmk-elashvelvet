"""Export only the Rasi BL and the matching self-update image, never full-chip HEX."""
from pathlib import Path
import json
import struct
import sys
from intelhex import IntelHex

build = Path(sys.argv[1]) / '_build/build-feather_nrf52840_rasi'
name = 'feather_nrf52840_rasi_bootloader-0.9.2-pad-replug'
h = IntelHex(str(build / (name + '.hex')))
assert all(0xf4000 <= a < 0xfe000 or 0x10001014 <= a < 0x1000101c
           for a in h.addresses()), h.segments()
assert sum(h[0x10001014 + i] << (8*i) for i in range(4)) == 0xf4000
assert sum(h[0x10001018 + i] << (8*i) for i in range(4)) == 0xfe000
assert b'Rasi_NRF_840BL' in h.tobinstr(start=0xf4000, end=0xfdfff)
out = Path('artifacts')
out.mkdir(exist_ok=True)
bl = IntelHex()
for address in h.addresses():
    if 0xf4000 <= address < 0xfe000:
        bl[address] = h[address]
bl.write_hex_file(str(out / 'pad52840_BL_ONLY.hex'))
# The old receiver requires UICR values as verification metadata. Its
# in_uicr_space branch validates them without programming UICR. Omitting
# this block explicitly aborts the update after the last block.
writer = (Path(sys.argv[1]) / 'src/usb/uf2/ghostfat.c').read_text()
assert 'state->update_bootloader && !state->has_uicr' in writer
assert 'state->has_uicr = true;' in writer
entries = [(address, bytes(bl[a] for a in range(address, address + 256)))
           for address in range(0xf4000, 0xfe000, 256)]
metadata = bytearray([255] * 256)
struct.pack_into('<II', metadata, 0x14, 0xf4000, 0xfe000)
# Send metadata first, so the final BL block can pass has_uicr validation.
entries.insert(0, (0x10001000, bytes(metadata)))
blocks = []
count = len(entries)
for index, (address, payload) in enumerate(entries):
    header = struct.pack('<8I', 0x0a324655, 0x9e5d5157, 0x2000,
                         address, 256, index, count, 0xd663823c)
    blocks.append(header + payload + bytes(220) + struct.pack('<I', 0x0ab16f30))
data = b''.join(blocks)
assert len(data) == 161 * 512
# CF2 board identifier must match the installed Rasi USB VID/PID.
assert struct.pack('<II', 208, 0x239a0029) in bl.tobinstr(start=0xfd800, end=0xfdfff)
(out / 'pad52840_BL_UPDATE.uf2').write_bytes(data)
(out / 'validation.json').write_text(json.dumps({
    'source_commit': 'b1d9a09665e9766b6fcd656e9788562c2cc72bac',
    'board': 'feather_nrf52840_rasi', 'bootloader_start': '0xf4000',
    'journal': '0xea000-0xeafff', 'application_start': '0x27000',
    'application_end_exclusive': '0xea000',
    'hardware_tested': False,
    'uicr_metadata_only': {'bootloader': '0xf4000', 'mbr_params': '0xfe000'},
    'warning': 'Keep existing S140 7.3.0. HEX is BL-only; no mass erase. '
               'UF2 is a bootloader self-update, not an application.'
}, indent=2))
