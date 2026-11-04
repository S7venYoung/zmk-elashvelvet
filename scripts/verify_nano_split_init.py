#!/usr/bin/env python3
"""Verify Bluetooth precedes split registration in the actual ARM ELF init table."""
from pathlib import Path
import struct
import sys

def symbols(path):
    blob = Path(path).read_bytes()
    if blob[:6] != b'\x7fELF\x01\x01':
        raise ValueError('Expected little-endian ELF32')
    shoff = struct.unpack_from('<I', blob, 32)[0]
    shentsize, shnum = struct.unpack_from('<HH', blob, 46)
    sections = [struct.unpack_from('<10I', blob, shoff+i*shentsize) for i in range(shnum)]
    found = {}
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        strings = sections[section[6]]
        names = blob[strings[4]:strings[4]+strings[5]]
        for off in range(section[4], section[4]+section[5], section[9]):
            name, value, size, info, other, index = struct.unpack_from('<IIIBBH', blob, off)
            end = names.find(b'\0', name)
            found[names[name:end].decode()] = value
    return found

def verify(path):
    syms = symbols(path)
    ble = syms['__init_zmk_ble_init']
    split = syms['__init_zmk_split_bt_central_init']
    if not ble < split:
        raise ValueError(f'Unsafe Nano initialization order: BLE={ble:#x} split={split:#x}')
    print(f'Nano initialization order verified: BLE={ble:#x} before split={split:#x}')

if __name__ == '__main__':
    verify(sys.argv[1])
