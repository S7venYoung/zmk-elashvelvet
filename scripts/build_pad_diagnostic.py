#!/usr/bin/env python3
"""Prepare a single Nano receiver diagnostic command; default is dry-run only."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]

def command(root=ROOT):
    targets = yaml.safe_load((root / 'build.yaml').read_text())['include']
    target = next(x for x in targets if x.get('artifact') == 'velvet_nano_dongle')
    assert target['board'] == 'nice_nano_k/nrf52833'
    snippets = target.get('snippet', '').split() + ['zmk-usb-logging']
    args = ['west', 'build', '-s', str(root / 'dependencies/zmk/app'),
            '-d', str(root / 'build/pad_dongle_diagnostic'), '-b', target['board'], '--',
            '-DZMK_CONFIG=' + str(root / 'config'),
            '-DZMK_EXTRA_MODULES=' + str(root),
            '-DSHIELD=' + target['shield'],
            '-DSNIPPET=' + ';'.join(snippets),
            '-DEXTRA_CONF_FILE=' + str(root / 'config/pad_dongle_diagnostic.conf')]
    return args + shlex.split(target.get('cmake-args', ''))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true', help='Actually compile; requires an initialized west workspace')
    args = parser.parse_args()
    cmd = command()
    print(json.dumps({'build': args.build, 'command': cmd}, ensure_ascii=False, indent=2))
    if args.build:
        subprocess.run(cmd, cwd=ROOT, check=True)
