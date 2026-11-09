#!/usr/bin/env python3
"""Verify the scan recovery callback and state are present in the ARM ELF."""
from pathlib import Path
import re
import struct
import sys


def symbols(path):
    blob = Path(path).read_bytes()
    if blob[:6] != b"\x7fELF\x01\x01":
        raise ValueError("Expected little-endian ELF32")
    shoff = struct.unpack_from("<I", blob, 32)[0]
    shentsize, shnum = struct.unpack_from("<HH", blob, 46)
    sections = [
        struct.unpack_from("<10I", blob, shoff + index * shentsize)
        for index in range(shnum)
    ]
    names = set()
    for section in sections:
        if section[1] != 2:
            continue
        strings = sections[section[6]]
        strings_data = blob[strings[4]:strings[4] + strings[5]]
        for offset in range(section[4], section[4] + section[5], section[9]):
            name, _, _, _, _, _ = struct.unpack_from("<IIIBBH", blob, offset)
            end = strings_data.find(b"\0", name)
            names.add(strings_data[name:end].decode())
    return names


def verify(path):
    found = {re.sub(r"\.lto_priv\.\d+$", "", name) for name in symbols(path)}
    required = {
        "start_scanning",
        "split_central_scan_retry_cb",
        "split_central_scan_retry_work",
        "is_scanning",
    }
    missing = required - found
    if missing:
        raise ValueError(f"Missing Nano split scan recovery symbols: {sorted(missing)}")
    print("Nano split scan recovery verified in linked ARM ELF")


if __name__ == "__main__":
    verify(sys.argv[1])
