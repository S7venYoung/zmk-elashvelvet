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
assert b'Rasi_NRF_840BL' in h.tobinstr(start=0xf4000, end=0xfdfff)
out = Path('artifacts')
out.mkdir(exist_ok=True)
bl = IntelHex()
for address in h.addresses():
    if 0xf4000 <= address < 0xfe000:
        bl[address] = h[address]
bl.write_hex_file(str(out / 'pad52840_BL_ONLY.hex'))
# Emit BL flash only: upstream's generic converter also emits padded UICR
# blocks. A BL self-update must not carry MBR/UICR or application payloads.
blocks = []
count = (0xfe000 - 0xf4000) // 256
for index, address in enumerate(range(0xf4000, 0xfe000, 256)):
    payload = bytes(bl[a] for a in range(address, address + 256))
    header = struct.pack('<8I', 0x0a324655, 0x9e5d5157, 0x2000,
                         address, 256, index, count, 0xd663823c)
    blocks.append(header + payload + bytes(220) + struct.pack('<I', 0x0ab16f30))
data = b''.join(blocks)
assert len(data) == count * 512
(out / 'pad52840_BL_UPDATE.uf2').write_bytes(data)
(out / 'validation.json').write_text(json.dumps({
    'source_commit': 'b1d9a09665e9766b6fcd656e9788562c2cc72bac',
    'board': 'feather_nrf52840_rasi', 'bootloader_start': '0xf4000',
    'journal': '0xea000-0xeafff', 'application_end_exclusive': '0xea000',
    'hardware_tested': False,
    'warning': 'Keep existing S140 7.3.0. HEX is BL-only; no mass erase. '
               'UF2 is a bootloader self-update, not an application.'
}, indent=2))
