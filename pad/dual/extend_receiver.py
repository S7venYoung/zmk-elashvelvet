"""Append Pad keys without changing existing Nano/Velvet bindings or positions."""
from pathlib import Path
import re

MARKER = 'PAD_DUAL_RECEIVER_EXTENSION'
def layer_blocks(text):
    match = re.search(r'\bkeymap\s*\{', text)
    if not match: raise ValueError('No keymap')
    start = match.end(); depth = 1; blocks = []; begin = None
    for i in range(start, len(text)):
        if text[i] == '{':
            if depth == 1: begin = i
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 1 and begin is not None: blocks.append((begin, i)); begin = None
            if depth == 0: return blocks, i
    raise ValueError('Unbalanced keymap')

def extend_keymap(text, count):
    if MARKER in text: return text
    blocks, end = layer_blocks(text)
    assert len(blocks) == 3, 'Existing Nano layer indices changed; review Pad Fn index'
    pad_base = '''
&kp KP_N7 &kp KP_N8 &kp KP_N9 &kp KP_PLUS
&kp KP_N4 &kp KP_N5 &kp KP_N6 &kp KP_MINUS
&kp KP_N1 &kp KP_N2 &kp KP_N3 &kp KP_ENTER
&mo 3 &kp KP_N0 &kp KP_DOT &kp BSPC
'''
    edits=[]
    for begin, limit in blocks:
        match=re.search(r'bindings\s*=\s*<(.*?)>;',text[begin:limit],re.S)
        assert match and len(re.findall(r'&\w+',match[1]))==count
        edits.append((begin+match.end(1),pad_base))
    fn = '\n'.join(['&trans'] * count) + '''
&bt BT_SEL 0 &bt BT_SEL 1 &bt BT_SEL 2 &bt BT_CLR
&out OUT_USB &out OUT_BLE &none &none
&none &none &none &none
&trans &kp KP_NUMLOCK &kp KP_DIVIDE &kp KP_MULTIPLY
'''
    edits.append((end,'\n        pad_fn { bindings = <\n'+fn+'>; };\n'))
    for at, addition in sorted(edits,reverse=True): text=text[:at]+addition+text[at:]
    return re.sub(r'(?m)^[ \t]+$', '', '#include <dt-bindings/zmk/outputs.h>\n/* '+MARKER+' */\n'+text)

def extend(root):
    root=Path(root); board=root/'boards/shields/velvet'
    overlay=board/'velvet_nano_dongle.overlay';s=overlay.read_text()
    if MARKER not in s:
        match=re.search(r'\bmap\s*=\s*<(.*?)>;',s,re.S)
        count=len(re.findall(r'RC\(',match[1]));assert count==61
        pad='\n'+'\n'.join(' '.join(f'RC({r+5},{c})' for c in range(4)) for r in range(4))+'\n'
        s=s[:match.end(1)]+pad+s[match.end(1):]
        s=s.replace('rows = <5>;', 'rows = <9>;')
        overlay.write_text(re.sub(r'(?m)^[ \t]+$', '', '/* '+MARKER+' */\n'+s))
        layout=board/'velvet-layouts.dtsi';s=layout.read_text();at=s.rfind(';\n    };')
        assert at>0
        extra='\n'+'\n'.join(f', <&key_physical_attrs 100 100 {2100+c*100} {r*100} 0 0 0>' for r in range(4) for c in range(4))+'\n'
        layout.write_text(re.sub(r'(?m)^[ \t]+$', '', s[:at]+extra+s[at:]))
        keymap=root/'config/velvet.keymap';keymap.write_text(extend_keymap(keymap.read_text(),count))
    conf=board/'velvet_nano_dongle.conf';s=conf.read_text()
    s=s.replace('CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS=2','CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS=3').replace('CONFIG_BT_MAX_CONN=3','CONFIG_BT_MAX_CONN=4').replace('CONFIG_BT_MAX_PAIRED=7','CONFIG_BT_MAX_PAIRED=8').replace('CONFIG_PROSPECTOR_EXPECTED_PERIPHERAL_COUNT=2','CONFIG_PROSPECTOR_EXPECTED_PERIPHERAL_COUNT=3')
    conf.write_text(s)
if __name__=='__main__':
    import sys
    extend(sys.argv[1])
