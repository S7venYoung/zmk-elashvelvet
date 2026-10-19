#!/usr/bin/env python3
"""Read-only Studio diagnostics. Usage: read_dashboard_status.py /dev/cu.usbmodem..."""
import os,sys,termios,fcntl,struct,select,time,json

def vi(n):
 out=bytearray()
 while n>127:out.append((n&127)|128);n>>=7
 out.append(n);return bytes(out)
def num(k,n):return vi(k*8)+vi(n)
def msg(k,b):return vi(k*8+2)+vi(len(b))+b
def parse(b):
 i=0;out={}
 def read():
  nonlocal i
  n=0;s=0
  while True:
   x=b[i];i+=1;n|=(x&127)<<s;s+=7
   if x<128:return n
 while i<len(b):
  t=read();k=t>>3;w=t&7
  if w==0:v=read()
  elif w==2:n=read();v=b[i:i+n];i+=n
  elif w in (1,5):n=8 if w==1 else 4;v=b[i:i+n];i+=n
  else:raise ValueError(w)
  out.setdefault(k,[]).append(v)
 return out
def one(p,k,d=None):return p.get(k,[d])[0]
path=sys.argv[1];fd=os.open(path,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
a=termios.tcgetattr(fd);a[0]=a[1]=a[3]=0;a[2]|=termios.CLOCAL|termios.CREAD;a[4]=a[5]=termios.B9600;termios.tcsetattr(fd,termios.TCSANOW,a);fcntl.ioctl(fd,0x80085402,struct.pack('Q',12500))
notes=[]
seq=100;frame=bytearray();started=False;escaped=False

def call(custom):
 global seq,frame,started,escaped
 seq+=1;b=num(1,seq)+msg(100,custom);wire=bytearray([171])
 for x in b:
  if x in (171,172,173):wire.append(172)
  wire.append(x)
 wire.append(173);os.write(fd,wire);end=time.monotonic()+7
 while time.monotonic()<end:
  if not select.select([fd],[],[],0.2)[0]:continue
  for x in os.read(fd,8192):
   if not started:
    if x==171:started=True;frame=bytearray();escaped=False
   elif escaped:frame.append(x);escaped=False
   elif x==172:escaped=True
   elif x==171:frame=bytearray()
   elif x==173:
    started=False;p=parse(bytes(frame));
    if 2 in p: notes.append(p[2][0])
    response=one(p,1)
    if response:
     p=parse(response)
     if one(p,1)==seq:return parse(one(p,100,b''))
   else:frame.append(x)
 raise TimeoutError('RPC response')
try:
 response=call(msg(1,b''));listing=parse(one(response,1,b''));subsystems={}
 for item in listing.get(1,[]):
  value=parse(item);subsystems[one(value,2,b'').decode()]=one(value,1,0)
 if 'velvet_display' not in subsystems:raise RuntimeError('No velvet_display subsystem on this device')
 response=call(msg(2,num(1,subsystems['velvet_display'])+msg(2,b'\x08\x01')))
 custom=parse(one(response,2,b''));payload=parse(one(custom,2,b''));data=one(payload,1,b'')
 if len(data)!=52 or data[0]!=1:raise RuntimeError('Firmware does not expose display diagnostics v1')
 u32=lambda offset:struct.unpack_from('<I',data,offset)[0]
 def peer(offset,age):
  p=data[offset:offset+12]
  if p[0]!=1:return {'seen':False}
  return {'seen':True,'side':p[1],'theme':p[2],'connected':bool(p[3]&1),
          'fresh':bool(p[3]&2),'received':struct.unpack_from('<I',p,4)[0],
          'drawn':struct.unpack_from('<I',p,8)[0],'ack_age_ms':u32(age)}
 print(json.dumps({'theme':data[1],'setting_result':struct.unpack_from('b',data,2)[0],
  'queue_result':struct.unpack_from('b',data,3)[0],'tx_count':u32(4),'ack_count':u32(8),
  'left':peer(12,36),'right':peer(24,40),'uptime_ms':u32(44)},indent=2))
finally:os.close(fd)
