#!/usr/bin/env python3
"""Validate right-before-display overlay order with Zephyr's actual DT parser."""
from pathlib import Path
import re
import sys
import tempfile

root=Path(__file__).resolve().parents[1]
zephyr=Path(sys.argv[1]).resolve()
module=Path(sys.argv[2]).resolve()
sys.path.insert(0,str(zephyr/'scripts/dts/python-devicetree/src'))
from devicetree import dtlib

for side in ('left','right'):
    source=(root/f'boards/shields/velvet/velvet_{side}.overlay').read_text()
    match=re.search(r'&nice_view_spi\s*\{.*?^\};',source,re.M|re.S)
    assert match,f'Missing {side} display SPI-node merge'
    panel=(module/'boards/shields/nice_view_custom/nice_view_custom.overlay').read_text()
    base='/dts-v1/; / { nice_view_spi: spi { #address-cells=<1>; #size-cells=<0>; }; };\n'
    old='&nice_view { serial-vcom-inversion; serial-vcom-interval=<33>; };\n'
    with tempfile.TemporaryDirectory() as tmp:
        file=Path(tmp)/'display.dts'
        file.write_text(base+old+panel)
        try:
            dtlib.DT(str(file))
        except dtlib.DTError as error:
            assert "undefined node label 'nice_view'" in str(error),error
        else:
            raise AssertionError('Negative control unexpectedly accepted forward reference')
        file.write_text(base+match[0]+'\n'+panel)
        tree=dtlib.DT(str(file))
        node=tree.label2node['nice_view']
        assert node.path=='/spi/ls0xx@0'
        assert 'serial-vcom-inversion' in node.props
        assert node.props['serial-vcom-interval'].to_num()==33
        assert node.props['width'].to_num()==160
        assert node.props['height'].to_num()==68
        assert node.props['spi-max-frequency'].to_num()==1000000
        assert tree.get_node('/chosen').props['zephyr,display'].to_path() is node
    print(f'{side} overlay order passed: SPI-node merge retains VCOM and display properties')
