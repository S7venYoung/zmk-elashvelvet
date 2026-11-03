import {UUID,parsePackage,DfuSession,connectDevice} from './dfu-core.mjs';
const $=id=>document.getElementById(id),supported=!!navigator.bluetooth&&window.isSecureContext;
let link=null,firmware=null,busy=false,selecting=false,loadGeneration=0;
function controls(){
  $('connect').disabled=!supported||busy||selecting;
  $('flash').disabled=!link?.device.gatt.connected||!firmware||busy||selecting||!$('confirm').checked;
  for(const id of ['file','confirm'])$(id).disabled=busy||selecting;
}
function update(message,percent){$('message').textContent=message;if(percent!==undefined){$('percent').textContent=percent+'%';$('progress').value=percent;}
  const lines=$('logs').textContent==='暂无记录'?[]:$('logs').textContent.split('\n');if(lines.at(-1)!==message)$('logs').textContent=[...lines,message].slice(-30).join('\n');}
async function loadFirmware(){
  const generation=++loadGeneration;
  firmware=null;controls();$('fileinfo').textContent='正在校验升级包……';
  try{
    const file=$('file').files[0];
    if(!file){$('fileinfo').textContent='请选择本板兼容的 Legacy DFU 应用 ZIP';return;}
    if(file.size>1048576)throw Error('ZIP 超过 1 MB');
    const data=new Uint8Array(await file.arrayBuffer());
    if(generation!==loadGeneration)return;firmware=parsePackage(data);$('fileinfo').textContent=`校验通过 · ${firmware.binary.length.toLocaleString()} 字节应用 · S132 6.1.1`;
  }catch(e){if(generation===loadGeneration){$('fileinfo').textContent=e.message;firmware=null;}}finally{controls();}
}
$('connect').onclick=async()=>{
  selecting=true;controls();
  try{
    // requestDevice must remain in the user click gesture, before any async work.
    const device=await navigator.bluetooth.requestDevice({filters:[{namePrefix:'Eyelash_WebDFU'}],optionalServices:[UUID.service]});
    if(link?.device.gatt.connected)link.device.gatt.disconnect();
    link=null;update('正在连接设备……');const next=await connectDevice(device);link=next;
    $('device').textContent=device.name||'Eyelash WebDFU';$('connection').textContent='蓝牙设备已连接';$('dot').className='online';$('phase').textContent='就绪';
    device.addEventListener('gattserverdisconnected',()=>{
      if(link?.device===device){$('connection').textContent='蓝牙已断开';$('dot').className='';if(!busy)$('phase').textContent='未连接';controls();}
    });update('设备已连接，请确认应用包',0);
  }catch(e){if(e.name==='NotFoundError')update('已取消选择，尚未刷写');else update('连接失败：'+e.message);}
  finally{selecting=false;controls();}
};
$('flash').onclick=async()=>{
  if(busy||!firmware||!link?.device.gatt.connected||!$('confirm').checked)return;
  busy=true;controls();$('phase').textContent='刷写中';
  try{await new DfuSession(link.device,link.control,link.packet,update).run(firmware.binary,firmware.init);$('phase').textContent='校验通过';}
  catch(e){update('刷写未完成：'+e.message+'。请重新按住 7＋9 开机后重试。');$('phase').textContent='未完成';}
  finally{busy=false;link=null;$('confirm').checked=false;controls();}
};
$('confirm').onchange=controls;
$('file').onchange=()=>{$('confirm').checked=false;loadFirmware();};
if(!supported)update('当前浏览器不支持 Web Bluetooth，请使用 Mac Chrome。');
controls();loadFirmware();
