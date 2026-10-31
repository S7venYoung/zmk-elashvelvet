/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdio.h>
#include "../themes/codex-system/left/render.h"
#include "../themes/codex-system/right/render.h"
static void save(const char*name,const uint8_t*p){FILE*f=fopen(name,"wb");assert(f);fprintf(f,"P4\n160 68\n");assert(fwrite(p,1,PANEL_BYTES,f)==PANEL_BYTES);fclose(f);}
int main(int argc,char**argv){
 struct {uint8_t before[16],p[PANEL_BYTES],after[16];}b;memset(&b,0xa5,sizeof(b));
 struct dashboard_status s={.keyboard={.connected=true,.battery_valid=true,.battery=78,.layer_valid=true,.side='L'},.count=12};
 uint8_t sample[DASH_DATA_SIZE]={1,63,1,24,70,82,64,0,0x7b,2,179,0,0,1,0x54,0x24,0,0};
 assert(dash_valid(sample,sizeof(sample)));memcpy(s.data,sample,sizeof(sample));
 for(unsigned flags=0;flags<64;flags++)for(unsigned value=0;value<=100;value++){
  s.data[1]=(uint8_t)flags;s.data[3]=s.data[4]=s.data[5]=s.data[6]=(uint8_t)value;
  s.keyboard.battery=(uint8_t)value;s.keyboard.layer=(uint8_t)(value%32);
  for(unsigned i=0;i<12;i++)s.history[i]=(uint8_t)((i*13+value)%101);
  codex_render(b.p,&s);system_render(b.p,&s);
  for(unsigned i=0;i<16;i++)assert(b.before[i]==0xa5&&b.after[i]==0xa5);
 }
 uint8_t theme_packet[DASH_PACKET_SIZE]={DASH_PACKET_VERSION,0,DASH_OUTPUT_USB,0};
 memcpy(theme_packet+DASH_PACKET_HEADER_SIZE,sample,sizeof(sample));
 assert(dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 theme_packet[1]=1;assert(dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 for(unsigned profile=1;profile<=5;profile++){
  theme_packet[2]=DASH_OUTPUT_BLE;theme_packet[3]=profile;
  assert(dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 }
 theme_packet[3]=0;assert(!dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 theme_packet[3]=6;assert(!dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 theme_packet[2]=DASH_OUTPUT_NONE;theme_packet[3]=0;assert(dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 theme_packet[3]=1;assert(!dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 theme_packet[2]=3;assert(!dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 theme_packet[2]=DASH_OUTPUT_USB;theme_packet[3]=0;theme_packet[1]=2;assert(!dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 theme_packet[1]=1;theme_packet[0]=1;assert(!dash_theme_packet_valid(theme_packet,sizeof(theme_packet)));
 assert(!dash_theme_packet_valid(NULL,DASH_PACKET_SIZE));assert(!dash_theme_packet_valid(theme_packet,3));
 uint8_t header_usb[PANEL_BYTES],header_ble[PANEL_BYTES],header_none[PANEL_BYTES];
 s.keyboard.output=DASH_OUTPUT_USB;s.keyboard.profile=0;codex_render(header_usb,&s);
 s.keyboard.output=DASH_OUTPUT_BLE;s.keyboard.profile=1;codex_render(header_ble,&s);
 s.keyboard.output=DASH_OUTPUT_NONE;s.keyboard.profile=0;codex_render(header_none,&s);
 assert(memcmp(header_usb,header_ble,sizeof(header_usb))&&memcmp(header_ble,header_none,sizeof(header_ble)));
 uint8_t previous_header[PANEL_BYTES];
 memset(previous_header,0,sizeof(previous_header));
 for(unsigned profile=1;profile<=5;profile++){
  s.keyboard.output=DASH_OUTPUT_BLE;s.keyboard.profile=profile;
  codex_render(b.p,&s);
  assert(memcmp(previous_header,b.p,sizeof(previous_header)));
  memcpy(previous_header,b.p,sizeof(previous_header));
  system_render(b.p,&s);
  for(unsigned i=0;i<16;i++)assert(b.before[i]==0xa5&&b.after[i]==0xa5);
 }
 s.keyboard.output=DASH_OUTPUT_USB;s.keyboard.profile=0;
 uint8_t polarity[PANEL_BYTES];memcpy(polarity,header_usb,sizeof(polarity));
 panel_invert(polarity);for(unsigned i=0;i<PANEL_BYTES;i++)assert(polarity[i]==(uint8_t)(header_usb[i]^255u));
 panel_invert(polarity);assert(!memcmp(polarity,header_usb,sizeof(polarity)));
 uint8_t aged[DASH_DATA_SIZE];
 dash_age_data(aged,sample,true,89999);assert(aged[1]==63&&dash_u32(aged+14)==9211);
 dash_age_data(aged,sample,true,90000);assert(aged[1]==0);
 dash_age_data(aged,sample,false,0);assert(aged[1]==0);
 uint8_t reset[DASH_DATA_SIZE];memcpy(reset,sample,sizeof(reset));dash_put32(reset+14,1);
 dash_age_data(aged,reset,true,2000);assert(dash_u32(aged+14)==0);
 uint8_t clock[DASH_DATA_SIZE];memcpy(clock,sample,sizeof(clock));
 dash_put32(clock+14,DASH_RESET_CLOCK|(19u*60u+20u));assert(dash_valid(clock,sizeof(clock)));
 dash_age_data(aged,clock,true,89999);assert(dash_u32(aged+14)==(DASH_RESET_CLOCK|1160u));
 dash_age_data(aged,clock,true,90000);assert(aged[1]==0);
 dash_put32(clock+14,DASH_RESET_CLOCK|1440u);assert(!dash_valid(clock,sizeof(clock)));
 dash_put32(clock+14,DASH_RESET_CLOCK);assert(dash_valid(clock,sizeof(clock)));
 uint8_t bad[DASH_DATA_SIZE];memcpy(bad,sample,sizeof(bad));bad[3]=101;assert(!dash_valid(bad,sizeof(bad)));
 memcpy(bad,sample,sizeof(bad));bad[1]=64;assert(!dash_valid(bad,sizeof(bad)));
 memcpy(bad,sample,sizeof(bad));bad[12]=bad[13]=0;assert(!dash_valid(bad,sizeof(bad)));
 memcpy(bad,sample,sizeof(bad));bad[8]=0xff;bad[9]=0x7f;assert(!dash_valid(bad,sizeof(bad)));
 assert(!dash_valid(NULL,DASH_DATA_SIZE));assert(!dash_valid(sample,17));
 if(argc>1){memcpy(s.data,sample,sizeof(sample));s.keyboard.battery=78;s.keyboard.layer=0;codex_render(b.p,&s);save(argv[1],b.p);}
 if(argc>2){s.keyboard.side='R';s.keyboard.battery=72;system_render(b.p,&s);save(argv[2],b.p);}
 if(argc>3){s.data[1]=0;system_render(b.p,&s);save(argv[3],b.p);}
 puts("Dashboard: flags/percentages, bounds, invalid packets and CPU temperature validation passed");
}
