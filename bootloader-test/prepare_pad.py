#!/usr/bin/env python3
"""Reuse Nano recovery logic on the pinned Rasi nRF52840 board."""
from pathlib import Path
import sys
from patch_usb_timeout import patch as patch_usb_timeout
from patch_uf2_finish import patch as patch_uf2_finish

root = Path(sys.argv[1])
here = Path(__file__).parent
board = root / "src/boards/feather_nrf52840_rasi"
assert 'MCU_SUB_VARIANT = nrf52840' in (board / 'board.mk').read_text()
assert '"Rasi_NRF_840BL"' in (board / 'board.h').read_text()

path = root / 'src/main.c'
source = path.read_text()

def replace(old, new):
    global source
    if source.count(old) != 1:
        raise SystemExit(f'Unexpected pinned Rasi source: {old}')
    source = source.replace(old, new, 1)

replace('#include "nrfx_nvmc.h"', '#include "nrfx_nvmc.h"\n'
        '#define NANO_JOURNAL_ADDR 0xea000u\n#include "nano_replug.h"\n'
        'static uint32_t pad_reset_reason;')
replace('int main(void) {', 'int main(void) {\n'
        '  pad_reset_reason = NRF_POWER->RESETREAS;')
# Clear only after the original reset-pin/DFU decision, preserving double-reset.
replace('  bool const valid_app = bootloader_app_is_valid();',
        '  bool const valid_app = bootloader_app_is_valid();\n'
        '  NRF_POWER->RESETREAS = pad_reset_reason;\n'
        '  if (valid_app && !dfu_start && nano_replug_boot(pad_reset_reason)) dfu_start = true;')
path.write_text(source)
for name in ['nano_replug.h', 'replug_policy.h']:
    (root / 'src' / name).write_text((here / name).read_text())
patch_usb_timeout(root / 'lib/sdk11/components/libraries/bootloader_dfu/bootloader.c')
patch_uf2_finish(root)
