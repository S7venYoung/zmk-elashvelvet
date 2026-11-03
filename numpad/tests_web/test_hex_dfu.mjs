import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {parseHex,parseFirmware,parsePackage,crc16} from '../web/dfu-core.mjs';
const require=createRequire(import.meta.url);globalThis.fflate=require('../web/vendor/fflate-0.8.3.js');
function record(address,type,data=[]){const bytes=[data.length,address>>8,address&255,type,...data];bytes.push((-bytes.reduce((a,b)=>a+b,0))&255);return ':'+bytes.map(x=>x.toString(16).padStart(2,'0')).join('').toUpperCase();}
const ext=(value)=>record(0,4,[value>>8,value&255]);
const vector=new Uint8Array(16);const words=new DataView(vector.buffer);words.setUint32(0,0x20010000,true);words.setUint32(4,0x26009,true);
const eof=record(0,1),good=[ext(2),record(0x6000,0,vector),eof].join('\n');
export async function runHexTests(real={}){
  const app=parseHex(good.replaceAll('\n','\r\n'));
  assert.equal(app.binary.length,16);assert.deepEqual(app.binary,vector);assert.equal(new DataView(app.init.buffer).getUint16(12,true),crc16(vector));
  assert.equal(parseFirmware(new TextEncoder().encode(good),'TEST.HEX').format,'HEX');
  const sparse=parseHex([ext(2),record(0x6000,0,vector),record(0x6020,0,[7]),eof].join('\n'));
  assert.equal(sparse.binary.length,36);assert.equal(sparse.binary[31],255);assert.equal(sparse.binary[32],7);assert.equal(sparse.binary[35],255);
  assert.throws(()=>parseHex(good.slice(0,-1)+(good.at(-1)==='0'?'1':'0')),/校验/);
  assert.throws(()=>parseHex(good.replace(eof,'')),/EOF/);
  assert.throws(()=>parseHex(good+'\n'+record(0,0,[0])),/EOF/);
  assert.throws(()=>parseHex([ext(2),record(0x6000,0,vector),record(0x6000,0,[1]),eof].join('\n')),/冲突/);
  assert.throws(()=>parseHex([ext(0),record(0,0,vector),eof].join('\n')),/应用 HEX/);
  assert.throws(()=>parseHex([ext(0x1000),record(0x1014,0,[0,0,0,0]),eof].join('\n')),/UICR/);
  assert.throws(()=>parseHex([ext(7),record(0x4000,0,vector),eof].join('\n')),/启动程序/);
  assert.throws(()=>parseHex([ext(6),record(0xd000,0,[0]),eof].join('\n')),/存储区/);
  assert.throws(()=>parseHex([ext(2),record(0x6004,0,[1,0x60,2,0]),eof].join('\n')),/向量/);
  const badVector=vector.slice();new DataView(badVector.buffer).setUint32(0,0x20040000,true);
  assert.throws(()=>parseHex([ext(2),record(0x6000,0,badVector),eof].join('\n')),/nRF52832/);
  if(real.hexPath&&real.zipPath){
    const hex=parseHex(await readFile(real.hexPath,'utf8')),zip=parsePackage(new Uint8Array(await readFile(real.zipPath)));
    assert.equal(hex.binary.length,zip.binary.length);assert.ok(hex.binary.every((b,i)=>b===zip.binary[i]));assert.equal(hex.init.length,zip.init.length);assert.ok(hex.init.every((b,i)=>b===zip.init[i]));
    return '13 HEX checks passed; user HEX binary and init packet exactly match verified nrfutil OTA package';
  }
  return '13 HEX parser and partition/CRC checks passed';
}
if(typeof process!=='undefined'&&process.argv[1]?.endsWith('test_hex_dfu.mjs'))console.log(await runHexTests());
