#!/usr/bin/env python3
"""Check that every built reset image contains the bootloader transition."""
from pathlib import Path
import sys
configs = list(Path(sys.argv[1] if len(sys.argv)>1 else 'build').glob('*/zephyr/.config'))
if len(sys.argv)>1:
    configs += list(Path(sys.argv[1]).glob('zephyr/.config'))
count=0
for cfg in configs:
    text=cfg.read_text()
    if 'CONFIG_SHIELD_SETTINGS_RESET=y\n' not in text:
        continue
    count+=1
    for option in ('ZMK_SETTINGS_RESET_ON_START','RETENTION_BOOT_MODE'):
        assert f'CONFIG_{option}=y\n' in text, (cfg,option)
    symbols=(cfg.parent/'zmk.map').read_text()
    for symbol in ('velvet_reset_settings','velvet_reset_finish','velvet_reset_enter_bootloader'):
        assert symbol in symbols, (cfg,symbol)
assert count, 'No settings_reset firmware found'
print(f'Checked {count} settings_reset image(s): erase + delayed bootloader transition linked')
