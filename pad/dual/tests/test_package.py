from pathlib import Path
import importlib.util,struct,tempfile,zlib
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package',root/'package.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
with tempfile.TemporaryDirectory() as tmp:
    d=Path(tmp)
    def image(base):return struct.pack('<II',0x20040000,base+9)+bytes(248)
    a=image(p.LAYOUT['SLOT_A_START']);b=image(p.LAYOUT['SLOT_B_START'])
    (d/'selector.bin').write_bytes(image(p.LAYOUT['SELECTOR_START'])[:16])
    p.emit(d/'a.uf2',p.LAYOUT['SLOT_A_START'],a);p.emit(d/'b.uf2',p.LAYOUT['SLOT_B_START'],b)
    p.package(d/'selector.bin',d/'a.uf2',d/'b.uf2',d/'dual.uf2')
    data=p.read_uf2(d/'dual.uf2',p.LAYOUT['SELECTOR_START'],p.LAYOUT['SLOT_B_LIMIT'])
    off=p.LAYOUT['SELECTOR_META']-p.LAYOUT['SELECTOR_START'];table=struct.unpack_from('<12I',data,off)
    assert table[:3]==(p.LAYOUT['META_MAGIC'],1,2)
    assert table[7]==zlib.crc32(a) and table[11]==zlib.crc32(b)
    for path,start,limit in [(d/'a.uf2',p.LAYOUT['SLOT_B_START'],p.LAYOUT['SLOT_B_LIMIT'])]:
        try:p.read_uf2(path,start,limit)
        except ValueError:pass
        else:raise AssertionError('Wrong slot accepted')
    damaged=bytearray((d/'a.uf2').read_bytes());damaged[-1]^=1;(d/'bad.uf2').write_bytes(damaged)
    try:p.read_uf2(d/'bad.uf2',p.LAYOUT['SLOT_A_START'],p.LAYOUT['SLOT_A_LIMIT'])
    except ValueError:pass
    else:raise AssertionError('Bad UF2 magic accepted')
    try:p.vector(image(p.LAYOUT['SLOT_B_START']),p.LAYOUT['SLOT_A_START'])
    except ValueError:pass
    else:raise AssertionError('Wrong reset vector accepted')
    assert p.LAYOUT['SLOT_B_LIMIT']<=p.LAYOUT['SLOT_B_NVS']<p.LAYOUT['BL_STAGING']
print('Pad packaging: vectors, CRC descriptors, protected ranges, malformed blocks and wrong slots passed')
