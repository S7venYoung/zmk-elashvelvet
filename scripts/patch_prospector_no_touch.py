"""Keep the pinned WALL-E theme usable without its optional touch backend."""
from pathlib import Path
import sys

def patch(file):
    p = Path(file)
    s = p.read_text()
    for old in ('#include <prospector_touch.h>', '    prospector_touch_attach(s);'):
        new = '#if IS_ENABLED(CONFIG_PROSPECTOR_TOUCH_ENABLED)\n' + old + '\n#endif'
        if new in s:
            continue
        if s.count(old) != 1:
            raise RuntimeError('Pinned WALL-E touch call layout changed: ' + old)
        s = s.replace(old, new)
    p.write_text(s)

if __name__ == '__main__':
    patch(sys.argv[1])
