"""Check that each firmware image targets its board's application partition."""

from pathlib import Path
import struct
import sys


def verify(path, family, start, limit):
    data = path.read_bytes()
    if not data or len(data) % 512:
        raise ValueError(f"{path}: invalid UF2 size")

    addresses = []
    for offset in range(0, len(data), 512):
        magic, magic2, flags, address, size, _, _, target = struct.unpack_from(
            "<8I", data, offset
        )
        end_magic, = struct.unpack_from("<I", data, offset + 508)
        if (magic, magic2, end_magic) != (0x0A324655, 0x9E5D5157, 0x0AB16F30):
            raise ValueError(f"{path}: invalid UF2 block at byte {offset}")
        if flags & 1:
            continue
        if not flags & 0x2000 or target != family:
            raise ValueError(f"{path}: wrong UF2 family at 0x{address:x}")
        if not 0 < size <= 476 or not start <= address < address + size <= limit:
            raise ValueError(f"{path}: block at 0x{address:x} exceeds its application partition")
        addresses.append(address)

    if not addresses or min(addresses) != start:
        raise ValueError(f"{path}: expected application to start at 0x{start:x}")
    print(f"{path.name}: application starts at 0x{start:x}")


if __name__ == "__main__":
    directory = Path(sys.argv[1])
    for name in ("velvet_nano_dongle", "settings_reset_nano"):
        verify(directory / f"{name}.uf2", 0x621E937A, 0x1000, 0x64000)
    for name in ("velvet_left_dongle", "velvet_right_dongle", "settings_reset"):
        verify(directory / f"{name}.uf2", 0xADA52840, 0x26000, 0xEC000)
