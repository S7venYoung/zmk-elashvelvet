"""Check generated hardware and roles, not just source configuration."""
from pathlib import Path
import re
import sys
p = Path(sys.argv[1])
config = (p / '.config').read_text()
for key in ('ZMK_SPLIT_ROLE_CENTRAL', 'ZMK_USB', 'ZMK_STUDIO', 'ZMK_DISPLAY'):
    assert f'CONFIG_{key}=y\n' in config, key
for key in ('PROSPECTOR_TOUCH_ENABLED', 'INPUT_CST816S', 'INPUT_CST816S_EV_DEVICE'):
    assert f'CONFIG_{key}=y\n' not in config, key
text = (p / 'zephyr.dts').read_text()
node = re.search(r'st7789v@0\s*\{([^{}]*)\}', text, re.S)
assert node, 'ST7789 panel missing'
for key, value in [('width',240), ('height',280), ('x-offset',0), ('y-offset',20), ('mipi-max-frequency',20000000)]:
    match = re.search(r'\b' + key + r'\s*=\s*<\s*(0x[0-9a-fA-F]+|[0-9]+)\s*>', node[1])
    assert match and int(match[1], 0) == value, key
for name in ('cst816s@15', 'apds9960@39'):
    match = re.search(re.escape(name) + r'\s*\{([^{}]*)\}', text, re.S)
    assert (match is None and name == "apds9960@39") or (match and 'status = "disabled"' in match[1]), name
# zephyr.dts may retain the XIAO connector specifier or show mapped GPIO pins.
for key, connector_pin, gpio_pin, active_low in [('dc-gpios',0,2,False), ('reset-gpios',1,28,True)]:
    match = re.search(re.escape(key) + r'\s*=\s*<\s*&([a-zA-Z0-9_]+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*>', text)
    assert match, key
    controller, pin, flags = match[1], int(match[2],0), int(match[3],0)
    assert (controller == 'xiao_d' and pin == connector_pin) or (controller == 'gpio0' and pin == gpio_pin), key
    assert bool(flags & 1) == active_low, key
print('1.69-inch receiver role, geometry, DC=D0/RES=D1 and absent touch: PASS')
