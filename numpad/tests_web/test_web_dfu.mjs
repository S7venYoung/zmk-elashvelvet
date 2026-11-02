import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {parsePackage,DfuSession,UUID,crc16} from '../web/dfu-core.mjs';
const require=createRequire(import.meta.url);
globalThis.fflate=require('../web/vendor/fflate-0.8.3.js');
export async function runTests(){
  let zip;
  try {zip=new Uint8Array(await readFile(new URL('../web/firmware/eyelash-numpad-peripheral-ota.zip',import.meta.url)));}
  catch(error){
    if(error.code!=='ENOENT')throw error;
    const binary=new Uint8Array(512),words=new DataView(binary.buffer);words.setUint32(0,0x20010000,true);words.setUint32(4,0x26009,true);
    const init=new Uint8Array(14),v=new DataView(init.buffer);v.setUint16(0,0x52,true);v.setUint16(2,0xadaf,true);v.setUint16(8,1,true);v.setUint16(10,0xb7,true);v.setUint16(12,crc16(binary),true);
    zip=fflate.zipSync({'manifest.json':new TextEncoder().encode(JSON.stringify({manifest:{dfu_version:0.5,application:{bin_file:'eyelash-numpad.bin',dat_file:'eyelash-numpad.dat'}}})), 'eyelash-numpad.bin':binary,'eyelash-numpad.dat':init});
  }
  const firmware=parsePackage(zip),expectedSize=firmware.binary.length;
  assert.ok(expectedSize===512 || expectedSize===178004);
  const definition=JSON.parse(await readFile(new URL('../web/web-dfu.json',import.meta.url),'utf8'));
  assert.equal(UUID.service,definition.service_uuid);assert.equal(UUID.control,definition.control_uuid);assert.equal(UUID.packet,definition.packet_uuid);
  const files=fflate.unzipSync(zip);files['eyelash-numpad.bin'][100]^=1;
  assert.throws(()=>parsePackage(fflate.zipSync(files)),/CRC16/);
  class Mock {
    constructor(status=1,bad=false){this.status=status;this.bad=bad;this.calls=[];this.sent=0;this.count=0;this.mode=0;this.listeners={};
      this.device={gatt:{connected:true,disconnect:()=>{this.device.gatt.connected=false;}},addEventListener:()=>{},removeEventListener:()=>{}};
      this.control={addEventListener:(type,fn)=>this.notify=fn,removeEventListener:()=>{},startNotifications:async()=>{},writeValueWithResponse:async d=>{
        this.calls.push([...d]);if(d[0]===1)this.mode=1;else if(d[0]===2&&d[1]===1)this.reply(2);else if(d[0]===3)this.mode=3;else if(d[0]===4)this.reply(4,this.status);else if(d[0]===5)this.device.gatt.connected=false;
      }};
      this.packet={writeValueWithoutResponse:async d=>{
        if(this.mode===1){this.total=new DataView(d.buffer,d.byteOffset,d.byteLength).getUint32(8,true);this.mode=2;this.reply(1);}
        else if(this.mode===3){assert.ok(d.length<=20);this.sent+=d.length;if(++this.count%8===0){const n=new Uint8Array(5);n[0]=0x11;new DataView(n.buffer).setUint32(1,this.sent-(this.bad?1:0),true);this.emit(n);}if(this.sent===this.total)this.reply(3);}
      }};
    }
    emit(d){this.notify({target:{value:new DataView(d.buffer)}});}
    reply(op,status=1){this.emit(new Uint8Array([0x10,op,status]));}
    session(events=[]){return new DfuSession(this.device,this.control,this.packet,(...args)=>events.push(args),async()=>{});}
  }
  const success=new Mock(),events=[];await success.session(events).run(firmware.binary,firmware.init);assert.equal(success.sent,expectedSize);assert.deepEqual(success.calls.at(-1),[5]);assert.equal(events.at(-1)[1],100);
  const bad=new Mock(1,true);await assert.rejects(()=>bad.session().run(firmware.binary,firmware.init),/长度不匹配/);assert.ok(!bad.calls.some(x=>x[0]===5));
  const fail=new Mock(5);await assert.rejects(()=>fail.session().run(firmware.binary,firmware.init),/拒绝 DFU/);assert.ok(!fail.calls.some(x=>x[0]===5));
  return '5 web checks passed: release ZIP + UUID contract, CRC rejection, full ACK transfer, bad receipt stop, failed validation stop';
}

if (typeof process !== 'undefined' && process.argv[1]?.endsWith("test_web_dfu.mjs")) console.log(await runTests());
