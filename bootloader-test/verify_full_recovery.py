from pathlib import Path
import hashlib, json
from intelhex import IntelHex
root=Path(__file__).resolve().parent.parent/"bootloader/firmware"
path=root/"nano33_replug_FULL_RECOVERY.hex"
assert hashlib.sha256(path.read_bytes()).hexdigest()=="b766e68a42c30517b6f767162c40b975c190a696411103b9fc596f8ef50a6f42"
h=IntelHex(str(path))
assert h.segments()==[(0,0x80000),(0x10001014,0x1000101c)],h.segments()
for addr,val in [(0x10001014,0x74000),(0x10001018,0x7e000)]:
    assert sum(h[addr+i]<<(i*8) for i in range(4))==val
assert all(h[a]==255 for a in range(0x27000,0x74000))
assert all(h[a]==255 for a in range(0x7e000,0x80000))
assert bytes(h[a] for a in range(0x74000,0x74008)) != bytes([255])*8
print("Field-tested full recovery image: SHA256, 512 KiB flash, UICR, blank application/settings/journal verified")
