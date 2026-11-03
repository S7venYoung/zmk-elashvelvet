// Eyelash application-only DFU; Legacy transport over a board-specific GATT service.
export const UUID = {
  service:'e7a11530-9d8f-4f12-8c72-72b5d7e90901',
  control:'e7a11531-9d8f-4f12-8c72-72b5d7e90901',
  packet:'e7a11532-9d8f-4f12-8c72-72b5d7e90901'
};
export function crc16(data) {
  let crc=0xffff;
  for (const byte of data) {crc^=byte<<8;for(let i=0;i<8;i++)crc=((crc&0x8000)?(crc<<1)^0x1021:crc<<1)&0xffff;}
  return crc;
}
export function parsePackage(zip) {
  if(zip.length>1048576)throw Error('ZIP 超过 1 MB');
  let count=0,total=0;
  const files=globalThis.fflate.unzipSync(zip,{filter:f=>{
    if(++count>3 || (total+=f.originalSize)>1048576 || f.name.includes('/') || f.name.includes('\\'))throw Error('升级包文件不符合要求');
    return true;
  }});
  if(count!==3 || !files['manifest.json'])throw Error('需要标准三文件 OTA ZIP');
  const manifest=JSON.parse(new TextDecoder().decode(files['manifest.json'])).manifest;
  if(!manifest || Object.keys(manifest).sort().join(',')!=='application,dfu_version' || manifest.dfu_version!==0.5)throw Error('只接受 Legacy 应用包，不接受启动程序或 SoftDevice 更新');
  const binary=files[manifest.application.bin_file],init=files[manifest.application.dat_file];
  return validateFirmware(binary,init);
}
function validateFirmware(binary,init) {
  if(!binary || binary.length<8 || binary.length>0x47000 || binary.length%4 || !init || init.length!==14)throw Error('应用大小或初始化包不符合要求');
  const words=new DataView(binary.buffer,binary.byteOffset,binary.byteLength),info=new DataView(init.buffer,init.byteOffset,init.byteLength);
  const sp=words.getUint32(0,true),reset=words.getUint32(4,true),entry=reset&~1;
  if(!(sp>0x20000000 && sp<=0x20010000 && sp%8===0 && (reset&1) && entry>=0x26000 && entry<0x26000+binary.length))throw Error('不是本板 nRF52832 / 0x26000 应用镜像');
  if(info.getUint16(0,true)!==0x52 || info.getUint16(2,true)!==0xadaf || info.getUint16(8,true)!==1 || info.getUint16(10,true)!==0xb7)throw Error('设备或 S132 6.1.1 要求不匹配');
  if(info.getUint16(12,true)!==crc16(binary))throw Error('固件 CRC16 校验失败');
  return {binary,init};
}
export function parseHex(text) {
  if(text.length>1048576)throw Error('HEX 超过 1 MB');
  const memory=new Map();let base=0,ended=false,maximum=0;
  for(const [index,raw] of text.split(/\r?\n/).entries()){
    const line=raw.trim();if(!line)continue;
    if(ended || !/^:[0-9a-fA-F]+$/.test(line) || (line.length-1)%2)throw Error(`HEX 第 ${index+1} 行格式或 EOF 错误`);
    const bytes=Uint8Array.from(line.slice(1).match(/../g),x=>parseInt(x,16));
    if(bytes.length<5 || bytes.length!==bytes[0]+5 || (bytes.reduce((a,b)=>a+b,0)&255))throw Error(`HEX 第 ${index+1} 行校验失败`);
    const count=bytes[0],address=bytes[1]*256+bytes[2],type=bytes[3];
    if(type===0){
      if(address+count>0x10000)throw Error('HEX 数据跨越 64 KiB 边界');
      for(let i=0;i<count;i++){
        const absolute=base+address+i,value=bytes[4+i];
        if(absolute<0x26000 || absolute>=0x6d000)throw Error('只接受应用 HEX（0x26000–0x6CFFF），不能包含 SoftDevice、启动程序、存储区或 UICR');
        if(memory.has(absolute) && memory.get(absolute)!==value)throw Error('HEX 包含冲突地址');
        memory.set(absolute,value);maximum=Math.max(maximum,absolute);
      }
    }else if(type===1 && count===0 && address===0){ended=true;}
    else if((type===2 || type===4) && count===2 && address===0){base=(bytes[4]*256+bytes[5])*(type===2?16:65536);}
    else if((type===3 || type===5) && count===4 && address===0){/* Vector table is authoritative. */}
    else throw Error('不支持或无效的 HEX 记录类型');
  }
  if(!ended || !memory.size)throw Error('HEX 缺少数据或 EOF');
  for(let i=0;i<8;i++)if(!memory.has(0x26000+i))throw Error('HEX 缺少应用向量表');
  const entry=(memory.get(0x26004)+memory.get(0x26005)*256+memory.get(0x26006)*65536+memory.get(0x26007)*16777216)&~1;
  if(!memory.has(entry))throw Error('HEX 缺少复位入口数据');
  const length=Math.ceil((maximum-0x26000+1)/4)*4;
  if(length>0x47000)throw Error('应用超出分区');
  const binary=new Uint8Array(length);binary.fill(255);
  for(const [address,value] of memory)binary[address-0x26000]=value;
  const init=new Uint8Array(14),view=new DataView(init.buffer);
  view.setUint16(0,0x52,true);view.setUint16(2,0xadaf,true);
  view.setUint32(4,0xffffffff,true);view.setUint16(8,1,true);
  view.setUint16(10,0xb7,true);view.setUint16(12,crc16(binary),true);
  return validateFirmware(binary,init);
}
export function parseFirmware(bytes,name='') {
  const hex=name.toLowerCase().endsWith('.hex') || bytes[0]===0x3a;
  const result=hex?parseHex(new TextDecoder('utf-8',{fatal:true}).decode(bytes)):parsePackage(bytes);
  return {...result,format:hex?'HEX':'ZIP'};
}

class Inbox {
  constructor(){this.queue=[];this.pending=null;this.error=null;}
  put(item){if(this.pending){const p=this.pending;this.pending=null;clearTimeout(p.timer);p.resolve(item);}else this.queue.push(item);}
  take(ms=60000){
    if(this.error)return Promise.reject(this.error);
    if(this.queue.length)return Promise.resolve(this.queue.shift());
    return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{this.pending=null;reject(Error('等待设备确认超时，已停止'));},ms);this.pending={resolve,reject,timer};});
  }
  close(error){this.error=error;if(this.pending){clearTimeout(this.pending.timer);this.pending.reject(error);this.pending=null;}}
}
export class DfuSession {
  constructor(device,control,packet,update=()=>{},delay=ms=>new Promise(r=>setTimeout(r,ms))){
    Object.assign(this,{device,control,packet,update,delay});this.responses=new Inbox();this.receipts=new Inbox();this.activated=false;
    this.onNotify=event=>{const v=event.target.value;const d=new Uint8Array(v.buffer,v.byteOffset,v.byteLength);
      if(d.length>=3 && d[0]===0x10)this.responses.put([d[1],d[2]]);
      else if(d.length===5 && d[0]===0x11)this.receipts.put(v.getUint32(1,true));};
    this.onDisconnect=()=>{const error=Error('设备连接已断开，刷写结果尚未确认');this.responses.close(error);this.receipts.close(error);};
  }
  command(...values){return this.control.writeValueWithResponse(new Uint8Array(values));}
  async reply(expected){const [op,status]=await this.responses.take();if(op!==expected || status!==1)throw Error(`设备拒绝 DFU：操作 ${op}，返回 ${status}`);}
  async run(binary,init){
    this.control.addEventListener('characteristicvaluechanged',this.onNotify);
    this.device.addEventListener('gattserverdisconnected',this.onDisconnect);
    try {
      await this.control.startNotifications();
      this.update('准备擦写应用分区',0);await this.command(1,4);
      const size=new Uint8Array(12);new DataView(size.buffer).setUint32(8,binary.length,true);
      await this.packet.writeValueWithoutResponse(size);await this.reply(1);
      await this.command(2,0);await this.packet.writeValueWithoutResponse(init);await this.command(2,1);await this.reply(2);
      await this.command(8,8,0);await this.command(3);
      for(let offset=0,number=1;offset<binary.length;offset+=20,number++){
        const chunk=binary.subarray(offset,offset+20),sent=offset+chunk.length;
        await this.packet.writeValueWithoutResponse(chunk);
        if(number%8===0 && sent<binary.length){
          const received=await this.receipts.take(20000);if(received!==sent)throw Error('设备确认的接收长度不匹配，已停止');
          this.update('正在传输',Math.round(sent/binary.length*950)/10);
        }
        await this.delay(3);
      }
      await this.reply(3);this.update('设备校验固件',96);await this.command(4);await this.reply(4);
      this.update('校验通过，正在重启',99);
      try{await this.command(5);}catch(error){if(this.device.gatt.connected)throw error;}
      this.activated=true;this.update('DFU 校验通过，已发送重启指令；请测试按键和 Dongle 连接',100);
    } finally {
      this.control.removeEventListener('characteristicvaluechanged',this.onNotify);
      this.device.removeEventListener('gattserverdisconnected',this.onDisconnect);
      if(this.device.gatt.connected)this.device.gatt.disconnect();
    }
  }
}
export async function connectDevice(device){
  const server=await device.gatt.connect();
  try{const service=await server.getPrimaryService(UUID.service);return {device,control:await service.getCharacteristic(UUID.control),packet:await service.getCharacteristic(UUID.packet)};}
  catch(error){server.disconnect();throw error;}
}
