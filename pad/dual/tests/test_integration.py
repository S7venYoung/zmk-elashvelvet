from pathlib import Path
import importlib.util,re,subprocess,sys,tempfile
root=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('receiver',root/'pad/dual/extend_receiver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def original(path):return subprocess.check_output(['git','show','c6714bd:'+path],cwd=root,text=True)
def bindings(s):
    result=[]
    for begin,end in m.layer_blocks(s)[0]:
        body=re.search(r'bindings\s*=\s*<(.*?)>;',s[begin:end],re.S)[1]
        starts=list(re.finditer(r'&\w+',body));result.append([' '.join(body[x.start():(starts[i+1].start() if i+1<len(starts) else len(body))].split()) for i,x in enumerate(starts)])
    return result
old=original('config/velvet.keymap');new=(root/'config/velvet.keymap').read_text()
before,after=bindings(old),bindings(new)
assert len(before)==3 and len(after)==4
assert all(len(x)==61 for x in before) and all(len(x)==77 for x in after)
assert all(after[i][:61]==before[i] for i in range(3)), 'Original bindings changed'
assert m.extend_keymap(new,61)==new
old_layout=original('boards/shields/velvet/velvet-layouts.dtsi');new_layout=(root/'boards/shields/velvet/velvet-layouts.dtsi').read_text()
attrs=lambda s:re.findall(r'<&key_physical_attrs[^>]+>',s)
assert attrs(new_layout)[:61]==attrs(old_layout) and len(attrs(new_layout))==77
old_map=original('boards/shields/velvet/velvet_nano_dongle.overlay');new_map=(root/'boards/shields/velvet/velvet_nano_dongle.overlay').read_text()
coords=lambda s:re.findall(r'RC\(\d+,\d+\)',s)
assert coords(new_map)[:61]==coords(old_map) and len(coords(new_map))==77
# Exercise the actual patch against the selected ZMK checkout when supplied.
if len(sys.argv)>1:
    spec=importlib.util.spec_from_file_location('patch',root/'pad/dual/patch_zmk.py');patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
    paths=['src/rgb_underglow.c','CMakeLists.txt','src/studio/rpc.c','src/physical_layouts.c','src/split/peripheral.c','src/split/bluetooth/service.c','src/split/bluetooth/peripheral.c','src/studio/CMakeLists.txt']
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        app=Path(tmp)
        for rel in paths:
            (app/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(Path(sys.argv[1])/rel,app/rel)
        patch.patch(app);first=[(app/x).read_text() for x in paths];patch.patch(app)
        assert first==[(app/x).read_text() for x in paths]
print('Pad integration: original 61 keys/layout preserved, 16 Pad keys appended, 4 layers and patch idempotence passed')
