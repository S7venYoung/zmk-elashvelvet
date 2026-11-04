#!/usr/bin/env python3
"""Trace settings load/commit without changing their ordering or return values."""
from pathlib import Path
import sys

MARKER = 'EYELASH_DIAGNOSTIC_INIT_TRACE'
DECL = ('/* ' + MARKER + ' */\n'
        'extern void eyelash_diagnostic_stage(unsigned stage, int result);\n'
        'extern void eyelash_diagnostic_settings(const char *name, int phase, int result);\n')

def patch_main(text):
    if MARKER in text:
        return text
    old = '    settings_subsys_init();\n    settings_load();'
    new = '''    eyelash_diagnostic_stage(9, 0);
    int diagnostic_init_rc = settings_subsys_init();
    eyelash_diagnostic_stage(10, diagnostic_init_rc);
    int diagnostic_load_rc = settings_load();
    eyelash_diagnostic_stage(11, diagnostic_load_rc);'''
    if text.count(old) != 1:
        raise ValueError('Unexpected main settings load sequence')
    return DECL + text.replace(old, new, 1)

def patch_settings(text):
    if MARKER in text:
        return text
    needle = '\t\trc = ch->h_set(name_key, len, read_cb, read_cb_arg);'
    if text.count(needle) != 1 or text.count('rc2 = ch->h_commit();') != 2:
        raise ValueError('Unexpected Zephyr settings callbacks')
    text = text.replace(needle, '\t\teyelash_diagnostic_settings(ch->name, 1, 0);\n' + needle +
                        '\n\t\teyelash_diagnostic_settings(ch->name, 2, rc);')
    # Both static and dynamic handler loops retain their original priorities.
    lines = []
    for line in text.splitlines(keepends=True):
        if line.strip() == 'rc2 = ch->h_commit();':
            indent = line[:len(line) - len(line.lstrip())]
            lines.append(indent + 'eyelash_diagnostic_settings(ch->name, 3, 0);\n')
            lines.append(line)
            lines.append(indent + 'eyelash_diagnostic_settings(ch->name, 4, rc2);\n')
        else:
            lines.append(line)
    return DECL + ''.join(lines)

if __name__ == '__main__':
    for path, patch in [(Path(sys.argv[1]), patch_main), (Path(sys.argv[2]), patch_settings)]:
        path.write_text(patch(path.read_text()))
