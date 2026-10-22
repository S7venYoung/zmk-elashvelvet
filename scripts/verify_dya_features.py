#!/usr/bin/env python3
"""Verify actual DYA-capable central builds, not just manifest presence."""
from pathlib import Path
import sys
required = ['ZMK_RUNTIME_TAPDANCE', 'ZMK_RUNTIME_TAPDANCE_STUDIO_RPC', 'ZMK_INPUT_STREAM_FEATURE', 'ZMK_INPUT_STREAM_FEATURE_STUDIO_RPC', 'ZMK_PHYSICAL_LAYOUTS_FEATURE', 'ZMK_PHYSICAL_LAYOUTS_FEATURE_STUDIO_RPC', 'ZMK_DEFAULT_LAYER', 'ZMK_DEFAULT_LAYER_STUDIO_RPC', 'ZMK_OS_DETECTION', 'ZMK_OS_DETECTION_STUDIO_RPC', 'ZMK_OS_DETECTION_USB', 'ZMK_OS_DETECTION_BLE', 'ZMK_DEFAULT_LAYER_OS_DETECTION', 'ZMK_KSCAN_DIAGNOSTICS', 'ZMK_KSCAN_DIAGNOSTICS_STUDIO_RPC', 'ZMK_KSCAN_DIAGNOSTICS_SPLIT', 'ZMK_CUSTOM_SETTINGS_STUDIO_RPC', 'ZMK_RUNTIME_MACRO', 'ZMK_RUNTIME_MACRO_STUDIO_RPC', 'ZMK_RUNTIME_COMBO', 'ZMK_RUNTIME_COMBO_STUDIO_RPC', 'ZMK_FAST_KEYMAP', 'ZMK_FAST_KEYMAP_STUDIO_RPC', 'ZMK_FAST_KEYMAP_DEFAULT_LAYER', 'ZMK_DEVICE_INFO', 'ZMK_DEVICE_INFO_STUDIO_RPC', 'ZMK_WATCHDOG', 'ZMK_WATCHDOG_STUDIO_RPC']
root=Path(sys.argv[1] if len(sys.argv)>1 else 'build')
configs=list(root.glob('*/zephyr/.config'))+list(root.glob('zephyr/.config'))
checked=0
for cfg in configs:
    text=cfg.read_text()
    if 'CONFIG_ZMK_STUDIO=y\n' not in text: continue
    checked+=1
    for name in required: assert f'CONFIG_{name}=y\n' in text,(cfg,name)
    dts=(cfg.parent/'zephyr.dts').read_text()
    assert 'cormoran,zmk-behavior-runtime-tapdance' in dts,cfg
    assert list(cfg.parent.parent.rglob('behavior_runtime_tapdance.c.obj')),cfg
assert checked or '--peripheral-only' in sys.argv,'No Studio central found'
print(f'DYA central capabilities checked: {checked}')
