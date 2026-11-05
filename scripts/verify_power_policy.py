#!/usr/bin/env python3
"""Verify merged firmware settings; source conf fragments do not prove precedence."""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'build')
for target in ('velvet_nano_dongle', 'velvet_left_dongle', 'velvet_right_dongle',
               'eyelash_numpad_peripheral'):
    path = root / target / 'zephyr/.config'
    lines = set(path.read_text().splitlines())
    if target == 'eyelash_numpad_peripheral':
        expected = ['# CONFIG_ZMK_SLEEP is not set', 'CONFIG_ZMK_IDLE_TIMEOUT=7200000',
                    '# CONFIG_ZMK_KSCAN_MATRIX_POLLING is not set']
        symbols = (path.parent / 'zmk.map').read_text()
        assert 'pad_advertising_timeout' in symbols, target
        assert 'pad_resume_advertising' in symbols, target
        assert 'eyelash_advertising_wake' in symbols, target
    else:
        expected = ['CONFIG_ZMK_SLEEP=y', 'CONFIG_ZMK_IDLE_SLEEP_TIMEOUT=7200000',
                    'CONFIG_ZMK_IDLE_TIMEOUT=15000']
    if target == 'velvet_nano_dongle':
        expected += ['CONFIG_ZMK_SPLIT_BLE_PREF_INT=6',
                     'CONFIG_ZMK_SPLIT_BLE_PREF_LATENCY=30',
                     'CONFIG_ZMK_SPLIT_BLE_PREF_TIMEOUT=400',
                     'CONFIG_ZMK_LOW_PRIORITY_THREAD_STACK_SIZE=4096',
                     'CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE=4096',
                     'CONFIG_ZMK_STUDIO_RPC_TX_BUF_SIZE=512',
                     'CONFIG_ZMK_CUSTOM_SETTINGS_LIST_NOTIFICATION_BATCH_SIZE=1',
                     'CONFIG_ZMK_CUSTOM_SETTINGS_LIST_NOTIFICATION_DELAY_MS=50']
    for value in expected:
        assert value in lines, (target, value)
    assert 'CONFIG_ZMK_BLE_CLEAR_BONDS_ON_START=y' not in lines, target
    assert 'CONFIG_ZMK_SETTINGS_RESET_ON_START=y' not in lines, target
    print(f'{target}: sleep policy and preserved settings verified')
