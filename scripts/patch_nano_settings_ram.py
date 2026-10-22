"""Bound nanopb metadata buffers for the 128 KiB Nano central.

The wire schema is unchanged. Two constraints per setting retain the range/type
metadata used by this configuration. Reject excess metadata rather than truncate.
"""
from pathlib import Path
import sys

def patch(root):
    root = Path(root)
    options = root / 'proto/cormoran/zmk/custom_settings/custom_settings.options'
    handler = root / 'src/studio/custom_settings_handler.c'
    old = 'cormoran.zmk.custom_settings.SettingMeta.constraints max_count:8'
    new = old.replace('max_count:8', 'max_count:2')
    text = options.read_text()
    if text.count(old) == 1:
        text = text.replace(old, new)
    elif text.count(new) != 1:
        raise RuntimeError('Custom Settings nanopb metadata layout changed')
    source = handler.read_text()
    anchor = '    for (size_t i = 0;\n         i < constraints_count && dest->constraints_count < ARRAY_SIZE(dest->constraints); i++) {'
    guard = ('    /* Nano metadata capacity: never silently omit validation constraints. */\n'
             '    if (constraints_count > ARRAY_SIZE(dest->constraints)) {\n'
             '        return -ENOMEM;\n'
             '    }\n\n')
    if guard not in source:
        if source.count(anchor) != 1:
            raise RuntimeError('Custom Settings metadata encoder changed')
        source = source.replace(anchor, guard + anchor)
    options.write_text(text)
    handler.write_text(source)

if __name__ == '__main__':
    patch(sys.argv[1])
