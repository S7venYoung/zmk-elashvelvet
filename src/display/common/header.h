/* SPDX-License-Identifier: MIT */
#pragma once
#include "pixels.h"
#include "dashboard_data.h"
/* 7x13 Bluetooth rune: one straight stem and symmetric 45-degree arms. */
static inline void panel_bluetooth_icon(uint8_t *p,int x,int y){
 static const uint8_t rows[13]={
  0x08,0x0c,0x0a,0x49,0x2a,0x1c,0x08,0x1c,0x2a,0x49,0x0a,0x0c,0x08};
 for(unsigned row=0;row<13;row++)for(unsigned col=0;col<7;col++)
  if(rows[row]&(0x40u>>col))px(p,x+(int)col,y+(int)row,false);
}
static inline void panel_header(uint8_t*p,struct panel_status s){
 char n[8];n[0]=s.side;n[1]=0;text(p,3,4,n,1);box(p,14,2,1,10,false);
 panel_bluetooth_icon(p,22,0);
 box(p,32,10,2,2,!s.connected);box(p,37,2,1,10,false);
 if(s.output==DASH_OUTPUT_USB){
  outline(p,44,1,6,6);box(p,45,2,1,2,false);box(p,48,2,1,2,false);outline(p,42,7,10,5);
  box(p,44,9,2,1,false);box(p,48,9,2,1,false);text(p,56,4,"USB",1);
 }else if(s.output==DASH_OUTPUT_BLE&&dash_output_valid(s.output,s.profile)){
  panel_bluetooth_icon(p,44,0);
  snprintf(n,sizeof(n),"BLE%u",s.profile);text(p,54,4,n,1);
 }else text(p,51,4,"--",1);
 box(p,78,2,1,10,false);
 outline(p,85,3,13,8);box(p,98,5,2,4,false);
 if(s.battery_valid)box(p,87,5,(int)s.battery*9/100,4,false);
 if(s.battery_valid)snprintf(n,sizeof(n),"%u%%",s.battery);else strcpy(n,"--%");
 text(p,103,4,n,1);box(p,129,2,1,10,false);
 if(s.layer_valid)snprintf(n,sizeof(n),"L%u",(unsigned)s.layer+1);else strcpy(n,"L--");
 text(p,134,4,n,1);box(p,1,14,158,1,false);
}
static inline void solid_bar(uint8_t*p,int x,int y,int w,int h,unsigned percent,bool valid){
 outline(p,x,y,w,h);
 if(valid){unsigned fill=(percent>100?100:percent)*(unsigned)(w-4)/100;box(p,x+2,y+2,(int)fill,h-4,false);}
}

/* Reverse the existing information-page polarity; keep cat rendering untouched. */
static inline void panel_invert(uint8_t *p){
 for(unsigned i=0;i<PANEL_BYTES;i++)p[i]^=0xffu;
}
