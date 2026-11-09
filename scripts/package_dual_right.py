"""Pack the selector and both relocated nice!nano applications as one UF2."""

from pathlib import Path
import re
import struct
import sys

from verify_uf2_addresses import verify


ROOT = Path(__file__).resolve().parents[1]
LAYOUT = {
    key: int(value, 16)
    for key, value in re.findall(
        r"^#define VELVET_(\w+) (0x[0-9a-f]+)$",
        (ROOT / "dual-mode/layout.h").read_text(),
        re.M,
    )
}
FAMILY = 0xADA52840
PAYLOAD_SIZE = 256


def read_image(path, start, limit):
    verify(path, FAMILY, start, limit)
    uf2 = path.read_bytes()
    blocks = []
    for offset in range(0, len(uf2), 512):
        flags, address, size = struct.unpack_from("<3I", uf2, offset + 8)
        if not flags & 1:
            blocks.append((address, uf2[offset + 32 : offset + 32 + size]))
    contents = bytearray()
    for address, payload in sorted(blocks):
        if address != start + len(contents):
            raise ValueError(f"{path}: non-contiguous application payload")
        contents.extend(payload)
    check_vector(path, contents, start, start + len(contents))
    return contents


def check_vector(name, image, start, limit):
    sp, pc = struct.unpack_from("<2I", image)
    if not (0x20000000 < sp <= 0x20040000 and sp % 8 == 0 and pc & 1 and start <= pc < limit):
        raise ValueError(f"{name}: invalid initial stack or reset vector for 0x{start:x}")


def package(build, output):
    start = LAYOUT["SELECTOR_START"]
    nano = LAYOUT["NANO_IMAGE_START"]
    host = LAYOUT["HOST_IMAGE_START"]
    limit = LAYOUT["HOST_SETTINGS_START"]
    selector_path = build / "velvet-right-selector.bin"
    selector = selector_path.read_bytes()
    if not 8 <= len(selector) <= nano - start:
        raise ValueError("Selector must fit in the first application page")
    check_vector(selector_path, selector, start, start + len(selector))
    nano_image = read_image(build / "velvet_right_dongle/zephyr/zmk.uf2", nano, host)
    host_image = read_image(build / "velvet_right_host_slot/zephyr/zmk.uf2", host, limit)

    size = host - start + len(host_image)
    block_count = (size + PAYLOAD_SIZE - 1) // PAYLOAD_SIZE
    image = bytearray(b"\xff" * (block_count * PAYLOAD_SIZE))
    image[:len(selector)] = selector
    image[nano - start : nano - start + len(nano_image)] = nano_image
    image[host - start : host - start + len(host_image)] = host_image

    with output.open("wb") as out:
        for block in range(block_count):
            offset = block * PAYLOAD_SIZE
            out.write(struct.pack("<8I", 0x0A324655, 0x9E5D5157, 0x2000, start + offset,
                                  PAYLOAD_SIZE, block, block_count, FAMILY))
            out.write(image[offset : offset + PAYLOAD_SIZE])
            out.write(bytes(476 - PAYLOAD_SIZE))
            out.write(struct.pack("<I", 0x0AB16F30))

    verify(output, FAMILY, start, limit)
    print(f"Right-hand bundle: Nano {len(nano_image)} bytes, host {len(host_image)} bytes")


if __name__ == "__main__":
    package(Path(sys.argv[1]), Path(sys.argv[2]))
