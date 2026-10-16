from pathlib import Path
from intelhex import IntelHex
import json,sys,shutil
root=Path(sys.argv[1]);mode=sys.argv[2]
images=list((root/"_build/build-feather_nrf52833_express").glob("*.hex"))
assert len(images)==1, images
h=IntelHex(str(images[0]))
allowed=lambda a: 0x74000<=a<0x7e000 or 0x10001014<=a<0x1000101c
assert all(allowed(a) for a in h.addresses()), h.segments()
assert h[0x10001014]+(h[0x10001015]<<8)+(h[0x10001016]<<16)+(h[0x10001017]<<24)==0x74000
out=Path("artifacts");out.mkdir(exist_ok=True)
# Keep MBR, application, settings and UICR untouched. Existing UICR must match.
bl=IntelHex()
for a in h.addresses():
    if 0x74000<=a<0x7e000:bl[a]=h[a]
bl.write_hex_file(str(out/f"nano33_{mode}_bootloader_ONLY_TEST.hex"))
report={"source_commit":"d7c55d99c97633a770c5536dc113e3849f3bc91e",
        "mode":mode,"segments":bl.segments(),"bootloader_start":"0x74000",
        "mbr_params":"0x7e000","application_start_without_softdevice":"0x1000",
        "journal_page_replug_only":"0x65000-0x65fff","hardware_tested":False,
        "warning":"BL-only TEST image. No full-chip erase. Preserve MBR/UICR/app/settings. No SoftDevice included."}
(out/"validation.json").write_text(json.dumps(report,indent=2))
for f in (root/"_build/build-feather_nrf52833_express").glob("*.out*"):
    shutil.copy(f,out/f.name)
print(json.dumps(report,indent=2))
