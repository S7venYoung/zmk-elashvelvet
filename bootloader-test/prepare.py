#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1])
mode=sys.argv[2]
here=Path(__file__).parent

def replace(path, old, new):
    s=path.read_text()
    if s.count(old)!=1:
        raise SystemExit(f"Unexpected source structure: {path}: {old[:70]}")
    path.write_text(s.replace(old,new,1))

if mode=="replug":
    # Disable unused Feather GPIO hardware on the keyless receiver.
    board=root/"src/boards/feather_nrf52833_express/board.h"
    s=board.read_text()
    import re
    s=re.sub(r"^#define LEDS_NUMBER.*$", "#define LEDS_NUMBER 0", s, flags=re.M)
    s=re.sub(r"^#define (?:LED_PRIMARY_PIN|LED_SECONDARY_PIN|LED_NEOPIXEL|NEOPIXELS_NUMBER|BOARD_RGB_BRIGHTNESS).*\n", "", s, flags=re.M)
    s=s.replace('"PIVOT_BL"','"Nano Dongle"').replace('"FTHV29BOOT"','"NANO DONGLE"')
    s += "\n#define ENABLE_DCDC_0 0\n#define ENABLE_DCDC_1 0\n"
    board.write_text(s)
    replace(root/"src/boards/boards.c", "void led_tick(void) {", "void led_tick(void) {\n  return; /* No LED hardware on the test receiver. */")
    replace(root/"src/boards/boards.c",
            "  button_init(BUTTON_DFU);\n  button_init(BUTTON_FRESET);",
            "  /* Keyless receiver: no Feather button GPIOs. */")
    main=root/"src/main.c"
    replace(main, '#include "nrfx_nvmc.h"', '#include "nrfx_nvmc.h"\n#include "nano_replug.h"\nstatic uint32_t nano_reset_reason;')
    replace(main, "int main(void) {", "int main(void) {\n  nano_reset_reason = NRF_POWER->RESETREAS;\n  NRF_POWER->RESETREAS = nano_reset_reason;")
    replace(main, "  dfu_start = dfu_start || button_pressed(BUTTON_DFU);",
            "  /* No DFU button on this receiver. */")
    replace(main, "  _ota_dfu = _ota_dfu || (button_pressed(BUTTON_DFU) && button_pressed(BUTTON_FRESET));",
            "  /* No hardware OTA buttons on this receiver. */")
    replace(main, "  bool const valid_app = bootloader_app_is_valid();",
            "  bool const valid_app = bootloader_app_is_valid();\n  if (valid_app && !dfu_start && nano_replug_boot(nano_reset_reason)) dfu_start = true;")
    from patch_usb_timeout import patch as patch_usb_timeout
    patch_usb_timeout(root/"lib/sdk11/components/libraries/bootloader_dfu/bootloader.c")
    for name in ["replug_policy.h","nano_replug.h"]:
        (root/"src"/name).write_text((here/name).read_text())
elif mode!="baseline":
    raise SystemExit("Unknown mode")
