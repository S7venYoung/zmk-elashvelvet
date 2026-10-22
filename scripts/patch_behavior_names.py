"""Normalize public behavior names without changing aliases, IDs or bindings."""
from pathlib import Path
import re
import sys

def patch(root):
    root = Path(root)
    for module, filename, node, name in (
        ('zmk-feature-runtime-macro', 'runtime_macro.dtsi', 'runtime_macro', 'Macro'),
        ('zmk-feature-runtime-tapdance', 'runtime_tapdance.dtsi', 'runtime_tapdance', 'Tap Dance'),
    ):
        file = root / module / 'dts/behaviors' / filename
        text = file.read_text()
        match = re.search(r'\b' + node + r'\s*\{([^{}]*)\}', text, re.S)
        if not match:
            raise RuntimeError(f'Unexpected behavior definition: {file}')
        body = match.group(1)
        if 'display-name' in body:
            body, count = re.subn(r'display-name\s*=\s*"[^"]*"\s*;', f'display-name = "{name}";', body)
            if count != 1:
                raise RuntimeError(f'Ambiguous display name: {file}')
        else:
            body = body.rstrip() + f'\n            display-name = "{name}";\n        '
        file.write_text(text[:match.start(1)] + body + text[match.end(1):])

if __name__ == '__main__':
    patch(sys.argv[1] if len(sys.argv) > 1 else 'dependencies')
