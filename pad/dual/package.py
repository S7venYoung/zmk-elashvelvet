"""Validate and package two relocated Pad images without BL/NVS payloads."""
from pathlib import Path
import json,re,struct,sys,zlib
ROOT=Path(__file__).resolve().parent
LAYOUT={k:int(v,16) for k,v in re.findall(r'^#define PAD_(\w+) (0x[0-9a-f]+)u$',(ROOT/'layout.h').read_text(),re.M)}
FAMILY=0xada52840

def vector(data,base):
    if len(data)<8: raise ValueError('Short image')
    sp,pc=struct.unpack_from('<II',data)
    if not(0x20000000<sp<=0x20040000 and sp%8==0 and pc&1 and base<=pc&~1<base+len(data)):
        raise ValueError(f'Invalid vector at {base:x}')

def read_uf2(path,start,limit):
    raw=Path(path).read_bytes();blocks={};numbers=set()
    if not raw or len(raw)%512: raise ValueError('Bad UF2 size')
    total=len(raw)//512
    for i in range(total):
        block=raw[i*512:(i+1)*512];a,b,flags,addr,size,n,count,family=struct.unpack_from('<8I',block)
        if (a,b)!=(0x0a324655,0x9e5d5157) or struct.unpack_from('<I',block,508)[0]!=0x0ab16f30:raise ValueError('UF2 magic')
        if flags!=0x2000 or family!=FAMILY or size!=256 or count!=total:raise ValueError('UF2 header')
        if n in numbers or addr in blocks or not 0<=n<total:raise ValueError('Duplicate block')
        if addr<start or addr+size>limit or addr%256:raise ValueError('UF2 outside image slot')
        blocks[addr]=block[32:32+size];numbers.add(n)
    data=bytearray()
    for addr,payload in sorted(blocks.items()):
        if addr!=start+len(data):raise ValueError('Non-contiguous image')
        data.extend(payload)
    vector(data,start);return bytes(data)

def emit(path,start,data):
    data=data+bytes([255])*((-len(data))%256);count=len(data)//256
    with Path(path).open('wb') as f:
        for i in range(count):
            f.write(struct.pack('<8I',0x0a324655,0x9e5d5157,0x2000,start+i*256,256,i,count,FAMILY))
            f.write(data[i*256:(i+1)*256]);f.write(bytes(220));f.write(struct.pack('<I',0x0ab16f30))

def package(selector,a_path,b_path,out):
    a=read_uf2(a_path,LAYOUT['SLOT_A_START'],LAYOUT['SLOT_A_LIMIT'])
    b=read_uf2(b_path,LAYOUT['SLOT_B_START'],LAYOUT['SLOT_B_LIMIT'])
    boot=Path(selector).read_bytes();start=LAYOUT['SELECTOR_START'];meta=LAYOUT['SELECTOR_META']
    if not 8<=len(boot)<=meta-start:raise ValueError('Selector overlaps descriptor table')
    vector(boot,start)
    data=bytearray([255])*(LAYOUT['SLOT_B_START']-start+len(b));data[:len(boot)]=boot
    descriptors=[]
    table=struct.pack('<4I',LAYOUT['META_MAGIC'],1,2,0)
    for mode,image,base in [(0,a,LAYOUT['SLOT_A_START']),(1,b,LAYOUT['SLOT_B_START'])]:
        data[base-start:base-start+len(image)]=image
        crc=zlib.crc32(image);table+=struct.pack('<4I',mode,base,len(image),crc)
        descriptors.append({'mode':mode,'start':hex(base),'size':len(image),'crc32':hex(crc)})
    data[meta-start:meta-start+len(table)]=table
    emit(out,start,data)
    read_uf2(out,start,LAYOUT['SLOT_B_LIMIT'])
    Path(out).with_suffix('.json').write_text(json.dumps({'images':descriptors,'default':'standalone','hardware_tested':False,'settings_included':False,'bootloader_included':False},indent=2))
if __name__=='__main__':package(*sys.argv[1:])
